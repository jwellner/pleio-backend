from core.lib import tenant_schema


def send_event_qr(attendee):
    from event.tasks import send_mail_with_qr_code
    send_mail_with_qr_code.delay(tenant_schema(), attendee.id)
