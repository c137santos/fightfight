from torneios.models_pydantic import Message


def test_create_message():
    message_data = {"message": "Hello, World!"}
    message = Message.parse_obj(message_data)
    assert message.message == "Hello, World!"


def test_message_validation_transform():
    numer_message_data = {"message": 123}  # Número em vez de string
    response = Message(**numer_message_data)  # precisa passar a dar errado
    assert response == Message(message="123")
