# Obtener la plantilla desde el campo x_studio_documento
plantilla = record.x_studio_documento

# Obtener el grupo desde el campo x_studio_grupo
grupo = record.x_studio_grupo

# Obtener los usuarios del grupo
usuarios = grupo.users

# Verificar que la plantilla tenga campos de firma
if not plantilla.sign_item_ids:
    log("La plantilla no tiene campos de firma definidos.")

# Obtener el rol desde el primer campo de la plantilla
rol_firma = plantilla.sign_item_ids[0].responsible_id
if not rol_firma:
    log("No se encontró un rol asignado al campo de firma.")

# Enviar la solicitud de firma a cada usuario del grupo
for usuario in usuarios:
    partner = usuario.partner_id
    if not partner:
        continue

    solicitud_firma = env['sign.request'].create({
        'template_id': plantilla.id,
        'reference': plantilla.display_name,
        'request_item_ids': [(0, 0, {
            'partner_id': partner.id,
            'role_id': rol_firma.id,
        })],
    })

    # Desuscribir al creador para evitar notificaciones de firma
    creador = solicitud_firma.create_uid.partner_id
    if creador:
        solicitud_firma.message_unsubscribe([creador.id])

    # Marcar como enviada
    solicitud_firma.write({'state': 'sent'})

    log("Solicitud de firma enviada a %s con la plantilla '%s'" % (
        usuario.name, plantilla.display_name
    ))
