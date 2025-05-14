for lead in records:
    lead.sudo().write({
        'won_status': 'pending',              # Lo reactiva como oportunidad activa
        'active': True,                       # Lo desarchiva
        'user_id': False,                     # Lo libera de vendedor
        'x_instancia': lead.x_instancia + 1,  # Le sube una instancia
        'stage_id': 1                         # Lo pone en etapa 1
    })
