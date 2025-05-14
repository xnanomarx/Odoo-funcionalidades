# Inicia el proceso de asignación de leads
user = env.user
Grupo = env['res.groups']

mensaje = ""
lead_asignado = False

def pertenece_a(nombre_grupo):
    grupo = Grupo.sudo().search([('name', '=', nombre_grupo)], limit=1)
    return grupo in user.groups_id

grupos_limite_instancia_0 = ['Supervisores - Team leader - Senior']

# Determinamos el tipo de usuario
es_pasante = pertenece_a('Vendedor pasante')
es_junior = pertenece_a('Vendedor junior')
es_home_office = pertenece_a('Home office')
es_superior = any(pertenece_a(g) for g in grupos_limite_instancia_0)
es_middle = pertenece_a('Vendedor middle')

# Inicializamos las variables de turno y contador
if es_junior or es_superior or es_middle:
    if not user.x_turno_actual:
        user.sudo().write({'x_turno_actual': 'siguiente' if es_junior else 'instancia0'})
    if user.x_contador_turno is None:
        user.sudo().write({'x_contador_turno': 0})

# Límites diarios y semanales
limite_diario = 20 if es_pasante else 10 if es_home_office else 12
limite_semanal = 120 if es_pasante else 35 if es_home_office else 65
limite_hora = 10 if es_pasante else 5

ahora = datetime.datetime.now() 
hace_una_hora = ahora - datetime.timedelta(hours=1)
hoy = datetime.date.today()
# hoy en hora local a UTC
zona_horaria_offset = datetime.timedelta(hours=3)
inicio_dia_local = datetime.datetime.combine(hoy, datetime.time(0, 0)) + zona_horaria_offset
fin_dia_local = inicio_dia_local + datetime.timedelta(days=1)
fecha_limite_junior = user.x_fecha_ascenso_junior
inicio_semana = hoy - datetime.timedelta(days=7)

if fecha_limite_junior and fecha_limite_junior > inicio_semana:
    inicio_semana = fecha_limite_junior

# Verificamos los leads ya asignados
leads_usuario = env['crm.lead'].sudo().search([('user_id', '=', user.id), ('active', '=', True)])

etapas_bloqueo = ['Bolillero ( 4 hs )', 'Contacto iniciado ( 48 hs )', 'Propuesta enviada ( 5 dias )', 'Seguimientos ( 100 leads máximo )']
leads_sin_actividad = leads_usuario.filtered(lambda l: not l.activity_ids and l.stage_id.name in etapas_bloqueo)
leads_vencidas = leads_usuario.filtered(lambda l: l.activity_state == 'overdue' and l.stage_id.name in etapas_bloqueo)

#Verificación de firmas pendientes
limite_fecha = ahora - datetime.timedelta(days=2)
solicitudes_firma_pendientes = env['sign.request.item'].sudo().search([
    ('partner_id', '=', user.partner_id.id),
    ('state', 'in', ['sent', 'expired']),
    ('create_date', '<=', limite_fecha),
    ('sign_request_id.template_id.id', '!=', 67),
], limit=1)

if solicitudes_firma_pendientes:
    mensaje = "No se te asignará ningún lead hasta que completes las firmas pendientes."
elif leads_sin_actividad or leads_vencidas:
    mensaje = "No se te asignará ningún lead hasta que resuelvas tus leads sin actividad o con actividades vencidas."
else:
    cantidad_hora = env['crm.lead'].sudo().search_count([
        ('x_ultimo_asignado_por_fecha', '=', user.id),
        ('x_fecha_asignacion', '>=', hace_una_hora),
        ('x_fecha_asignacion', '<=', ahora),
        ('active', 'in', [True, False])
    ])
    
    # Leads asignados automáticamente HOY a este usuario (por el botón de pedir)
    cantidad_hoy = env['crm.lead'].sudo().search_count([
        ('x_ultimo_asignado_por_fecha', '=', user.id),
        ('x_fecha_asignacion', '>=', inicio_dia_local),
        ('x_fecha_asignacion', '<', fin_dia_local),
        ('active', 'in', [True, False])
    ])

    # Leads asignados automáticamente en los últimos 7 días a este usuario
    cantidad_semana = env['crm.lead'].sudo().search_count([
        ('x_ultimo_asignado_por_fecha', '=', user.id),
        ('x_fecha_asignacion', '>=', inicio_semana),
        ('x_fecha_asignacion', '<', hoy + datetime.timedelta(days=1)),
        ('active', 'in', [True, False])
    ])

    if cantidad_semana >= limite_semanal:
        mensaje = f"Ya alcanzaste tu límite semanal de {limite_semanal} leads."
    elif cantidad_hora >= limite_hora:
        mensaje = "Se detecta uso indebido del sistema. Evitar el uso repetitivo del bolillero para mantener la calidad de sus datos."
    elif cantidad_hoy >= limite_diario:
        mensaje = f"Ya alcanzaste tu límite diario de {limite_diario} leads."
    else:
        for instancia in range(0, 30):  # Búsqueda de leads por instancia

            # Control para pasantes y home office
            if es_pasante and instancia < 4:
                continue
            if es_home_office and instancia < 3:
                continue

            # Control por turno para juniors
            if es_junior:
                if instancia == 0 and user.x_turno_actual != 'instancia0':
                    continue
                elif instancia > 0 and user.x_turno_actual != 'siguiente':
                    continue
            # Control por turno para middle
            elif es_middle:
                if instancia == 0 and user.x_turno_actual != 'instancia0':
                    continue
                elif instancia > 0 and user.x_turno_actual != 'siguiente':
                    continue
            # Control por turno para superiores
            elif es_superior:
                if instancia == 0:
                    if user.x_turno_actual != 'instancia0' or user.x_contador_turno >= 3:
                        continue
                else:
                    if user.x_turno_actual != 'siguiente':
                        continue

            # Buscar lead de la instancia actual
            lead = env['crm.lead'].sudo().search([ 
                ('user_id', '=', False),
                ('x_historial_vendedores', 'not in', user.id),
                ('won_status', '=', 'pending'),
                ('x_instancia', '=', instancia),
                ('active', '=', True),
                ('x_studio_selection_field_6m3_1hubhopum', 'not in', ['Mejorar Salud', 'Referido'])
            ], limit=1, order='create_date ASC')

            # Si no se encuentra un lead de la instancia 0, y el usuario está en turno 'instancia0', buscamos uno de la siguiente instancia
            if instancia == 0 and not lead:
                lead = env['crm.lead'].sudo().search([ 
                    ('user_id', '=', False),
                    ('x_historial_vendedores', 'not in', user.id),
                    ('won_status', '=', 'pending'),
                    ('x_instancia', '>', instancia),  # Buscamos una instancia siguiente
                    ('active', '=', True),
                    ('x_studio_selection_field_6m3_1hubhopum', 'not in', ['Mejorar Salud', 'Referido'])
                ], limit=1, order='create_date ASC')

            if lead:
                vals = {'user_id': user.id, 'type': 'opportunity' if lead.type == 'lead' else lead.type}
                lead.sudo().write(vals)
                # Guardar fecha de asignación personalizada y actualizar historial
                lead.sudo().write({
                    'x_fecha_asignacion': lead.date_open,
                    'x_ultimo_asignado_por_fecha': user.id,
                    'x_historial_vendedores': [(4, user.id)]
                })
                lead_asignado = True
                mensaje = "Se te asignó un nuevo lead.\nActualizá la página para verlo en el tablero."
                
                # Actualizamos turno y contador para el siguiente turno
                if es_junior:
                    if instancia > 0:
                        nuevo_contador = user.x_contador_turno + 1
                        if nuevo_contador >= 3:
                            user.sudo().write({'x_turno_actual': 'instancia0', 'x_contador_turno': 0})
                        else:
                            user.sudo().write({'x_contador_turno': nuevo_contador})
                    else:  # instancia == 0
                        user.sudo().write({'x_turno_actual': 'siguiente', 'x_contador_turno': 0})
                elif es_middle:
                    if instancia == 0:
                        user.sudo().write({'x_turno_actual': 'siguiente'})
                    else:
                        user.sudo().write({'x_turno_actual': 'instancia0'})
                elif es_superior:
                    if instancia == 0:
                        nuevo_contador = user.x_contador_turno + 1
                        if nuevo_contador >= 3:
                            user.sudo().write({'x_turno_actual': 'siguiente', 'x_contador_turno': 0})
                        else:
                            user.sudo().write({'x_contador_turno': nuevo_contador})
                    else:  # instancia > 0
                        user.sudo().write({'x_turno_actual': 'instancia0', 'x_contador_turno': 0})
                break

        if not lead_asignado and not mensaje:
            mensaje = "No hay leads disponibles para asignar."
    
# Resultado final con notificación
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


