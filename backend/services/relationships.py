"""Relationship reports using the shared atomic calculation service."""
import uuid
from fastapi import HTTPException
from pydantic import ValidationError
from domain.relationships import RelationshipRequest, build_relationships
from services.paid_calculations import PaidCalculations


def metadata(data):
    return ('compatibility' if data.kind == 'pair' else 'group_compatibility',
            'Совместимость пары' if data.kind == 'pair' else 'Совместимость группы', data.main.birth_date)


class Relationships(PaidCalculations):
    def __init__(self, db):
        super().__init__(db, namespace='relationship_requests', report_key='relationship_report',
                         prices={'pair': 'compatibility_pair', 'group': 'group_compatibility'},
                         build=build_relationships, metadata=metadata)

    async def legacy(self, uid, kind, raw):
        main = {'name': raw.get('person1_name') or 'Человек 1', 'birth_date': raw.get('person1_birth_date')}
        people = [{'name': raw.get('person2_name') or 'Человек 2', 'birth_date': raw.get('person2_birth_date')}]
        if kind == 'group':
            main = {'name': raw.get('main_person_name') or 'Вы', 'birth_date': raw.get('main_person_birth_date')}
            people = raw.get('people')
        price = raw.get('expected_cost')
        if price is None:
            price = (await self.catalog(uid))[kind]
        if price is None:
            raise HTTPException(503, 'Стоимость расчёта временно недоступна')
        try:
            data = RelationshipRequest.model_validate({'kind': kind, 'main': main, 'people': people,
                'request_id': raw.get('request_id') or str(uuid.uuid4()), 'expected_cost': price})
        except ValidationError:
            raise HTTPException(422, 'Проверьте имена и даты рождения: ДД.ММ.ГГГГ, начиная с 1900 года')
        return (await self.calculate(uid, data))['results']['legacy']

