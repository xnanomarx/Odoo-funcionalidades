user = env.user
Grupo = env['res.groups']

mensaje = ""
lead_asignado = False

def pertenece_a(nombre_grupo):
    grupo = Grupo.sudo().search([('name', '=', nombre_grupo)], limit=1)
    return grupo in user.group_ids

grupos_limite_instancia_0 = ['Vendedor senior', 'Supervisores', 'Team leader']

es_pasante = pertenece_a('Vendedor pasante')
es_junior = pertenece_a('Vendedor junior')
es_home_office = pertenece_a('Home office')

limite_diario = 20 if es_pasante else 10 if es_home_office else 12
limite_semanal = 120 if es_pasante else 35 if es_home_office else 55

hoy = datetime.date.today()
hace_7_dias = hoy - datetime.timedelta(days=7)

leads_usuario = env['crm.lead'].sudo().search([('user_id', '=', user.id), ('active', '=', True)])

etapas_bloqueo = [
    'Cartera de clientes',
    'Prospectado',
    'Seguimientos',
    'Gestionando venta ( vendedor )'
]

leads_sin_actividad = leads_usuario.filtered(
    lambda l: not l.activity_ids and l.stage_id.name in etapas_bloqueo
)
leads_vencidas = leads_usuario.filtered(
    lambda l: l.activity_state == 'overdue' and l.stage_id.name in etapas_bloqueo
)

if leads_sin_actividad or leads_vencidas:
    mensaje = "No se te asignará ningún lead hasta que resuelvas tus leads sin actividad o con actividades vencidas."
else:
    cantidad_hoy = env['crm.lead'].sudo().search_count([
        ('x_historial_vendedores', 'in', user.id),
        ('x_fecha_asignacion', '>=', hoy),
        ('x_fecha_asignacion', '<', hoy + datetime.timedelta(days=1)),
        ('active', 'in', [True, False])  # Incluye tanto activos como no activos 
    ])

    cantidad_semana = env['crm.lead'].sudo().search_count([
        ('x_historial_vendedores', 'in', user.id),
        ('x_fecha_asignacion', '>=', hoy - datetime.timedelta(days=7)),
        ('x_fecha_asignacion', '<', hoy + datetime.timedelta(days=1)),
        ('active', 'in', [True, False])  # Incluye tanto activos como no activos 
    ])

    cantidad_instancia0 = env['crm.lead'].sudo().search_count([
        ('x_historial_vendedores', 'in', user.id),
        ('x_instancia', '=', 0),
        ('x_fecha_asignacion', '>=', hoy),
        ('x_fecha_asignacion', '<', hoy + datetime.timedelta(days=1)),
        ('active', 'in', [True, False])  # Incluye tanto activos como no activos 
    ])

    if cantidad_semana >= limite_semanal:
        mensaje = f"Ya alcanzaste tu límite semanal de {limite_semanal} leads."
    elif cantidad_hoy >= limite_diario:
        mensaje = f"Ya alcanzaste tu límite diario de {limite_diario} leads."
    else:
        for instancia in range(0, 20):
            if es_pasante and instancia < 3:
                continue
            if es_home_office and instancia < 3:
                continue

            if instancia == 0:
                if any(pertenece_a(g) for g in grupos_limite_instancia_0):
                    if cantidad_instancia0 >= 7:
                        continue
                elif es_junior:
                    if cantidad_instancia0 >= 2:
                        continue

            lead = env['crm.lead'].sudo().search([
                ('user_id', '=', False),
                ('x_historial_vendedores', 'not in', user.id),
                ('won_status', '=', 'pending'),
                ('x_instancia', '=', instancia),
                ('active', '=', True),
            ], limit=1, order='create_date ASC')

            if lead:
                # Asignar usuario y convertir en oportunidad si es necesario
                vals = {
                    'user_id': user.id,
                    'type': 'opportunity' if lead.type == 'lead' else lead.type
                }
                lead.sudo().write(vals)

                # Guardar fecha de asignación personalizada y actualizar historial
                lead.sudo().write({
                    'x_fecha_asignacion': lead.date_open,
                    'x_historial_vendedores': [(4, user.id)]
                })

                lead_asignado = True
                mensaje = "Se te asignó un nuevo lead.\nActualizá la página para verlo en el tablero."
                break

    if not lead_asignado and not mensaje:
        mensaje = "No hay leads disponibles para asignar."

params = {
    'title': 'Resultado',
    'message': mensaje,
    'sticky': True,
    'type': 'success' if lead_asignado else 'warning',
}

if lead_asignado:
    params['next'] = {
        'type': 'ir.actions.client',
        'tag': 'reload',
    }

action = {
    'type': 'ir.actions.client',
    'tag': 'display_notification',
    'params': params,
}
