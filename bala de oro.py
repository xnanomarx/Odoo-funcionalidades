ahora = datetime.datetime.now() - datetime.timedelta(hours=3)  # Ajuste manual a GMT-3
hoy = datetime.date.today()

user = env.user

# Actualizamos el usuario después de los cambios
user = env.user

# Obtener los valores actuales
if not user.x_bala_de_oro_ultima:
    # Si nunca se ha usado, le damos margen para usarla ahora mismo (como si la última vez hubiera sido hace 2 horas)
    hace_dos_horas = ahora - datetime.timedelta(hours=2)
    user.sudo().write({
        'x_bala_de_oro_ultima': hace_dos_horas,
        'x_balas_de_oro_hoy': 0
    })

# Reiniciar contador si cambió el día
if user.x_bala_de_oro_ultima.date() != hoy:  # Usamos .date() para comparar solo la fecha
    contador = 0  # Si cambió el día, reiniciamos el contador
else:
    contador = user.x_balas_de_oro_hoy  # Recuperamos el contador actual de balas de oro

mensaje = "No se encontró ningún lead de instancia 0 para asignar."
lead_asignado = False

# Si ya usó sus 4 balas de oro, no puede pedir más
if contador >= 4:
    mensaje = "Ya usaste tus 4 balas de oro de hoy. Volvé mañana."
else:
    if user.x_bala_de_oro_ultima:  # Solo calculamos el "próximo intento" si ya ha usado alguna bala de oro
        # Sumamos 1 hora a la última vez que usó la bala de oro
        proximo_uso = user.x_bala_de_oro_ultima + datetime.timedelta(minutes=20)  # Esto es correcto, timedelta suma duración
    else:
        proximo_uso = ahora  # Si nunca ha usado, el próximo intento es el mismo momento

    if ahora < proximo_uso:
        hora_formateada = proximo_uso.strftime("%H:%M")  # Mostramos la hora formateada
        mensaje = f"¡Paciencia! Tu próximo intento es a las {hora_formateada}."
    else:
        # Buscar el primer lead pendiente de instancia 0
        lead = env['crm.lead'].sudo().search([ 
            ('user_id', '=', False),
            ('x_historial_vendedores', 'not in', user.id),
            ('x_instancia', '=', 0),
            ('won_status', '=', 'pending'),
            ('active', '=', True),
            ('x_studio_selection_field_6m3_1hubhopum', 'not in', ['Mejorar Salud', 'Referido'])
        ], limit=1, order='create_date ASC')

        if lead:
            lead.sudo().write({
                'user_id': user.id,
                'type': 'opportunity' if lead.type == 'lead' else lead.type,
                'x_historial_vendedores': [(4, user.id)]  # Agregar al historial de vendedores
            })

            user.sudo().write({
                'x_bala_de_oro_ultima': ahora,  # Actualizamos la última vez que se usó la bala de oro
                'x_balas_de_oro_hoy': contador + 1  # Incrementamos el contador
            })

            mensaje = "¡Usaste tu bala de oro! Se te asignó un lead."
            lead_asignado = True

params = {
    'title': 'Bala de oro',
    'message': mensaje,
    'sticky': True,
    'type': 'success' if lead_asignado else 'warning',
}

if lead_asignado:
    params['next'] = {
        'type': 'ir.actions.client',
        'tag': 'reload',  # Recargar para que el cambio se refleje
    }

action = {
    'type': 'ir.actions.client',
    'tag': 'display_notification',
    'params': params,
}




