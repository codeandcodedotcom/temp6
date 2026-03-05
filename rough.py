SERVICE_BUS_NAMESPACE = "mcseundevmsgsb01.servicebus.windows.net"
SERVICE_BUS_QUEUE = "ems-standard"
SERVICE_BUS_PUBLISHER = "project-charter-service"


import json
from azure.identity import DefaultAzureCredential
from azure.servicebus import ServiceBusClient, ServiceBusMessage
from app.config.settings import (
    SERVICE_BUS_NAMESPACE,
    SERVICE_BUS_QUEUE,
    SERVICE_BUS_PUBLISHER,
)


class ServiceBusPublisher:

    def __init__(self):
        self.client = ServiceBusClient(
            fully_qualified_namespace=SERVICE_BUS_NAMESPACE,
            credential=DefaultAzureCredential(),
        )

    def publish_email(self, payload: dict):

        message = ServiceBusMessage(
            json.dumps(payload),
            content_type="application/json",
        )

        # REQUIRED BY THEIR PLATFORM
        message.application_properties = {
            "Publisher": SERVICE_BUS_PUBLISHER
        }

        with self.client.get_queue_sender(queue_name=SERVICE_BUS_QUEUE) as sender:
            sender.send_messages(message)


publisher = ServiceBusPublisher()


def build_charter_email(recipients: list[str], charter_id: str) -> dict:

    link = f"https://your-ui-url/charter/{charter_id}"

    body = f"""
    <html>
    <body>
        <p>A new project charter has been created.</p>
        <p>Click the link below to view the charter:</p>
        <a href="{link}">{link}</a>
    </body>
    </html>
    """

    return {
        "Recipients": recipients,
        "BccRecipients": None,
        "Subject": "New Project Charter Created",
        "Body": body,
        "IsHtml": True,
        "Sender": None,
        }



    from app.utils.service_bus import publisher
from app.utils.email_payload import build_charter_email


def create_charter(...):

    charter = save_charter_to_db(...)

    recipients = [
        "user1@company.com",
        "user2@company.com"
    ]

    payload = build_charter_email(
        recipients=recipients,
        charter_id=str(charter.id)
    )

    publisher.publish_email(payload)

    return charter
