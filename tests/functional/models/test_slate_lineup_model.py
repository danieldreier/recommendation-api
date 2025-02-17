from tests.functional.test_dynamodb_base import TestDynamoDBBase

from unittest.mock import patch

import app.config
from app.models.slate_lineup import SlateLineupModel
from app.models.slate_config import SlateConfigModel
from app.models.slate_experiment import SlateExperimentModel
from app.models.slate_lineup_experiment import SlateLineupExperimentModel
from app.models.slate_lineup_config import SlateLineupConfigModel

# First slate
slate_config_id = 'test-slate-config-id'
slate_experiment = SlateExperimentModel('test-ex', 'test-ex-desc', ['top15', 'thompson-sampling'],
                                        ['test-candidate-id'])
slate_config_model = SlateConfigModel(slate_config_id, 'test-this-slate', 'test-desc', experiments=[slate_experiment])

# Second slate
slate_config_id_2 = 'test-slate-config-id-2'
slate_experiment_2 = SlateExperimentModel('test-ex-2', 'test-ex-desc-2', ['top15', 'thompson-sampling'],
                                        ['test-candidate-id-2'])
slate_config_model_2 = SlateConfigModel(slate_config_id_2, 'test-this-slate-2', 'test-desc-2',
                                        experiments=[slate_experiment_2])

# Lineup with one slate
slate_lineup_config_id = 'test-slate_lineup-config-id'
slate_lineup_experiment = SlateLineupExperimentModel('test-ex', 'test-ex-desc', ['top15'], [slate_config_id])
slate_lineup_config_model = SlateLineupConfigModel(slate_lineup_config_id, 'test-desc', [slate_lineup_experiment])

# Lineup with two slates
slate_lineup_config_id_2 = 'test-slate_lineup-config-id-2'
slate_lineup_experiment_2 = SlateLineupExperimentModel('test-ex-2', 'test-ex-desc-2', ['top15'],
                                                     slates=[slate_config_id, slate_config_id_2])
slate_lineup_config_model_2 = SlateLineupConfigModel(slate_lineup_config_id_2, 'test-desc', [slate_lineup_experiment_2])

# Slates by id
slate_configs_by_id = {
    slate_config_id: slate_config_model,
    slate_config_id_2: slate_config_model_2,
}


class TestSlateLineupModel(TestDynamoDBBase):

    @patch('app.models.slate_lineup_config.SlateLineupConfigModel.find_by_id', return_value=slate_lineup_config_model)
    @patch('app.models.slate_config.SlateConfigModel.find_by_id', return_value=slate_config_model)
    async def test_get_slate_lineup(self, slate_config, slate_lineup_config):
        self.candidateSetTable.put_item(Item={
            "id": "test-candidate-id",
            "version": 1,
            "created_at": 1612907252,
            "candidates": [
                {
                    "feed_id": 1,
                    "item_id": 3208490410,
                    "publisher": "hbr.org"
                }
            ]
        })

        slate_lineup = await SlateLineupModel.get_slate_lineup(slate_lineup_config_id)

        assert slate_lineup.id == slate_lineup_config_id
        assert slate_lineup.slates[0].id == slate_config_id
        assert len(slate_lineup.requestId) == 36  # length of uuid4
        assert slate_lineup.slates[0].recommendations[0].item.item_id == '3208490410'

    @patch('app.models.slate_lineup_config.SlateLineupConfigModel.find_by_id', return_value=slate_lineup_config_model)
    @patch.object(SlateConfigModel, 'SLATE_CONFIGS_BY_ID', slate_configs_by_id)
    @patch.object(app.config, 'qa_slate_map', {slate_config_id: slate_config_id_2})
    async def test_get_slate_lineup_for_qa_user(self, slate_lineup_config):
        self.candidateSetTable.put_item(Item={
            "id": "test-candidate-id",
            "version": 1,
            "created_at": 1612907252,
            "candidates": [
                {
                    "feed_id": 1,
                    "item_id": 3208490410,
                    "publisher": "hbr.org"
                }
            ]
        })

        self.candidateSetTable.put_item(Item={
            "id": "test-candidate-id-2",
            "version": 1,
            "created_at": 1612907252,
            "candidates": [
                {
                    "feed_id": 1,
                    "item_id": 11,
                    "publisher": "getpocket.com"
                },
                {
                    "feed_id": 1,
                    "item_id": 12,
                    "publisher": "getpocket.com"
                }
            ]
        })

        qa_user_id = app.config.qa_user_ids[0]
        slate_lineup = await SlateLineupModel.get_slate_lineup(slate_lineup_config_id, user_id=qa_user_id)

        assert slate_lineup.id == slate_lineup_config_id
        assert slate_lineup.slates[0].id == slate_config_id_2  # The slate is replace based on qa_slate_map.
        assert slate_lineup.slates[0].recommendations[0].item.item_id == '11'

    @patch('app.models.slate_lineup_config.SlateLineupConfigModel.find_by_id', return_value=slate_lineup_config_model)
    @patch('app.models.slate_config.SlateConfigModel.find_by_id', return_value=slate_config_model)
    async def test_get_slate_lineup_limited_recs(self, slate_config, slate_lineup_config):
        self.candidateSetTable.put_item(Item={
            "id": "test-candidate-id",
            "version": 1,
            "created_at": 1612907252,
            "candidates": [
                {
                    "feed_id": 1,
                    "item_id": 3208490410,
                    "publisher": "hbr.org"
                },
                {
                    "feed_id": 1,
                    "item_id": 3208650410,
                    "publisher": "hbr.org"
                },
                {
                    "feed_id": 1,
                    "item_id": 32084925410,
                    "publisher": "hbr.org"
                }
            ]
        })

        slate_lineup = await SlateLineupModel.get_slate_lineup(slate_lineup_config_id, recommendation_count=1)
        assert len(slate_lineup.slates[0].recommendations) == 1

    @patch('app.models.slate_lineup_config.SlateLineupConfigModel.find_by_id', return_value=slate_lineup_config_model)
    @patch('app.models.slate_config.SlateConfigModel.find_by_id', return_value=slate_config_model)
    async def test_get_slate_lineup_no_slates(self, slate_config, slate_lineup_config):
        self.candidateSetTable.put_item(Item={
            "id": "test-candidate-id",
            "version": 1,
            "created_at": 1612907252,
            "candidates": [
                {
                    "feed_id": 1,
                    "item_id": 3208490410,
                    "publisher": "hbr.org"
                }
            ]
        })

        slate_lineup = await SlateLineupModel.get_slate_lineup(slate_lineup_config_id, slate_count=0)
        assert len(slate_lineup.slates) == 0

    @patch.object(SlateConfigModel, 'SLATE_CONFIGS_BY_ID', slate_configs_by_id)
    @patch('app.models.slate_lineup_config.SlateLineupConfigModel.find_by_id', return_value=slate_lineup_config_model_2)
    async def test_get_slate_lineup_dedupe_recs(self, slate_lineup_config):
        self.candidateSetTable.put_item(Item={
            "id": "test-candidate-id",
            "version": 1,
            "created_at": 1612907252,
            "candidates": [
                {
                    "feed_id": 1,
                    "item_id": 10,
                    "publisher": "hbr.org"
                },
                {
                    "feed_id": 1,
                    "item_id": 11,
                    "publisher": "hbr.org"
                },
            ]
        })

        self.candidateSetTable.put_item(Item={
            "id": "test-candidate-id-2",
            "version": 1,
            "created_at": 1612907252,
            "candidates": [
                {
                    "feed_id": 1,
                    "item_id": 11,
                    "publisher": "hbr.org"
                },
                {
                    "feed_id": 1,
                    "item_id": 12,
                    "publisher": "hbr.org"
                }
            ]
        })

        slate_lineup = await SlateLineupModel.get_slate_lineup(slate_lineup_config_id_2)
        assert len(slate_lineup.slates[0].recommendations) == 2
        assert len(slate_lineup.slates[1].recommendations) == 1

        assert {'10', '11'} == {recommendation.item_id for recommendation in slate_lineup.slates[0].recommendations}
        assert slate_lineup.slates[1].recommendations[0].item_id == '12'
