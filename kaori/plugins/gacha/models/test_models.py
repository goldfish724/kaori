import re
from pathlib import Path
from unittest.mock import Mock
from sqlalchemy.orm import Session

from kaori.plugins.users import User

from kaori.skills import LocalFileUploader

from kaori.adapters.slack import SlackMessage, SlackAdapter
from .Image import Image
from .Card import Card
from uuid import uuid4


def test_card_hydration(db_session: Session):
    from ..engine.test.cards.meme_cards import sachiko
    expected_max_hp = sachiko.max_hp

    name = str(uuid4())

    user = User(name=f'{name}-user',
                slack_id=f'{name}-slack-id',
                api_key=str(uuid4()))

    db_session.add(user)
    db_session.commit()

    card = Card(name=name,
                slug=name,
                owner=user.id,
                creation_thread_channel=f'ch-{name}',
                creation_thread_ts=f'ts-{name}')

    card.set_rarity(sachiko.rarity)

    card.stupid = sachiko.stupid
    card.baby = sachiko.baby
    card.cursed = sachiko.cursed
    card.horny = sachiko.horny
    card.clown = sachiko.clown
    card.feral = sachiko.feral

    card.primary_nature = str(sachiko.nature[0])
    card.secondary_nature = str(sachiko.nature[1])

    db_session.add(card)
    db_session.commit()

    db_session.refresh(card)

    assert bool(card.id) is True
    assert bool(card.name) is True
    assert bool(card.rarity) is True
    assert bool(card.primary_nature) is True
    assert bool(card.secondary_nature) is True

    assert card.engine is not None
    assert card.engine.max_hp == expected_max_hp

    db_session.flush()


def test_image_from_slack(db_session: Session):
    image_file = Path(__file__) \
        .parent \
        .joinpath('../../../../tests/fixtures/kaori.png') \
        .resolve()

    file = {
        'id': 'ZZZ'
    }

    slack_user = str(uuid4())

    message = SlackMessage({
        'event': {
            'user': slack_user,
            'files': [file],
        },
    })

    user = User(name=str(uuid4()),
                slack_id=slack_user,
                api_key=str(uuid4()))

    db_session.add(user)
    db_session.commit()

    def fake_downloader(*args, **kwargs):
        return 'fake.png', image_file.open('rb')

    img = Image.from_slack_message(message=message,
                                   session=db_session,
                                   slack_adapter=Mock(spec=SlackAdapter,
                                                      client=None),
                                   uploader=LocalFileUploader(),
                                   slack_file_downloader=fake_downloader)

    db_session.add(img)
    db_session.commit()

    assert re.match(r'https://kaori-img.ngrok.io/fake-sha512-\S+.png', img.url) is not None
    assert img.owner == user.id

    db_session.flush()