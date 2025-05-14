remitente = env.user.partner_id
if record.x_studio_enviar_como_usuario_corporativo:
    usuario_corp = env['res.users'].browse(391)  # ID del usuario corporativo
    remitente = usuario_corp.partner_id

cuerpo = record.x_studio_mensaje or ""

# Si hay un canal seleccionado, se publica ahí el mensaje general
if record.x_studio_canal:
    record.x_studio_canal.message_post(
        body=cuerpo,
        author_id=remitente.id,
        message_type='comment'
    )

# Lógica para difusión
if record.x_studio_es_difusin:
    if record.x_studio_canal:
        objetivos = record.x_studio_canal.channel_partner_ids.filtered(lambda p: p.id != remitente.id)
    else:
        objetivos = record.x_studio_objetivos_del_mensaje.filtered(lambda p: p.id != remitente.id)

    for partner in objetivos:
        canal_info = env['discuss.channel'].search([
            ('channel_type', '=', 'chat'),
            ('channel_partner_ids', 'in', [partner.id]),
            ('channel_partner_ids', 'in', [remitente.id]),
        ], limit=1)

        if not canal_info:
            canal = env['discuss.channel'].create({
                'name': 'Canal con %s' % partner.name,
                'channel_type': 'chat',
                'channel_partner_ids': [(6, 0, [partner.id, remitente.id])],
            })
        else:
            canal = canal_info[0]

        canal.message_post(
            body=cuerpo,
            author_id=remitente.id,
            message_type='comment'
        )
