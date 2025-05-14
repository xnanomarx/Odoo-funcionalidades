for record in records:
    # Cambiar el estado de aprobación
    record.write({
        'request_status': 'approved',
        'user_status': 'approved'  # Asegurar que se refleje en la vista kanban
    })
    # Marcar las actividades como completadas
    record.activity_ids.action_done()
    
    # Enviar notificación al solicitante
    if record.create_uid and record.create_uid.partner_id:
        record.message_post(
            body="Tu solicitud de aprobación ha sido aceptada.",  # Corregido
            partner_ids=[record.create_uid.partner_id.id],  # Notificar al solicitante
            message_type="notification",
            subtype_xmlid="mail.mt_comment",
            subject="Notificación de Aprobación",
        )
