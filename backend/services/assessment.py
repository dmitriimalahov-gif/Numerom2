from domain.assessment import build_assessment, public_questions, TITLE, DESCRIPTION
from services.paid_calculations import PaidCalculations


class Assessment(PaidCalculations):
    def __init__(self, db):
        super().__init__(db, namespace='assessment_requests', key_prefix='assessment:', report_key='assessment_report',
            prices={'assessment': 'quiz_completion'}, build=build_assessment,
            metadata=lambda data: ('numerology_assessment', TITLE, ''))

    async def catalog(self, uid):
        return {**await super().catalog(uid), 'title': TITLE, 'description': DESCRIPTION, 'questions': public_questions()}
