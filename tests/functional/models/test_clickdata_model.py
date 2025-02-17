from decimal import Decimal

from tests.functional.test_dynamodb_base import TestDynamoDBBase
from app.models.metrics.recommendation_metrics_factory import RecommendationMetricsFactory
from app.config import dynamodb as dynamodb_config

class TestRecommendationMetricsModel(TestDynamoDBBase):

    async def test_get_metrics_by_item(self):
        await self._put_metrics_fixtures()

        metrics = await RecommendationMetricsFactory(dynamodb_config["endpoint_url"]).get("1234-ABCD",
                                                                                          ["666666", "333333"])
        assert len(metrics) == 2
        # assert "default" in metrics  # this has been removed until priors are added back in
        assert "666666" in metrics
        assert "333333" in metrics
        assert "999999" not in metrics

    async def test_get_cached_metrics_by_item(self):
        await self._put_metrics_fixtures()

        # Get and cache metrics.
        # - 666666, 333333, and "default" all exist in the database
        # - 111111 doesn't exist, but will be created later
        # - foobar doesn't exist, and will not be created
        metrics = await RecommendationMetricsFactory(dynamodb_config["endpoint_url"]).get("1234-ABCD",
                                                                          ["111111", "666666", "333333", "foobar"])
        assert len(metrics) == 2
        # assert metrics["default"].trailing_28_day_opens == 200  # no priors as above
        assert metrics["333333"].trailing_28_day_opens == 33
        assert metrics["666666"].trailing_28_day_opens == 66
        assert "foobar" not in metrics
        # "111111" does not exist yet, and is therefore not returned
        assert "111111" not in metrics

        # Change clicks from 66 to 67 for "1234-ABCD/666666"
        self.recommendationMetricsTable.update_item(
            Key={"recommendations_pk": "666666/1234-ABCD"},
            UpdateExpression="set trailing_28_day_opens=:c, trailing_28_day_impressions=:i",
            ExpressionAttributeValues={':c': Decimal(67), ':i': Decimal(1000)})

        # Insert a new item, that wasn't there before.
        self.recommendationMetricsTable.put_item(Item={
            "recommendations_pk": "111111/1234-ABCD",
            "trailing_28_day_opens": "1",
            "trailing_28_day_impressions": "5",
            "trailing_14_day_opens": "0",
            "trailing_14_day_impressions": "0",
            "trailing_7_day_opens": "0",
            "trailing_7_day_impressions": "0",
            "trailing_1_day_opens": "0",
            "trailing_1_day_impressions": "0",
            "created_at": "0",
            "expires_at": "0"
        })

        # The click value in the database has changed. Assert that we're getting the same click value from cache.
        metrics = await RecommendationMetricsFactory(dynamodb_config["endpoint_url"]).get("1234-ABCD",
                                                                                          ["111111", "666666", "333333"])
        assert len(metrics) == 2
        # assert metrics["default"].clicks == 200  # no priors as above
        assert metrics["333333"].trailing_28_day_opens == 33
        assert metrics["666666"].trailing_28_day_opens == 66
        assert "foobar" not in metrics
        # "111111" exists in the database, but not in the cache.
        assert "111111" not in metrics

        await super().clear_caches()

        # The cache has been cleared. Assert that we're getting the new click values from the database.
        metrics = await RecommendationMetricsFactory(dynamodb_config["endpoint_url"]).get("1234-ABCD",
                                                                                          ["111111", "666666", "333333"])
        assert len(metrics) == 3
        # assert metrics["default"].clicks == 200  # no default prior key
        assert metrics["333333"].trailing_28_day_opens == 33
        assert metrics["666666"].trailing_28_day_opens == 67
        assert "foobar" not in metrics
        assert metrics["111111"].trailing_28_day_opens == 1

    async def _put_metrics_fixtures(self):
        self.recommendationMetricsTable.put_item(Item={
            "recommendations_pk": "default/1234-ABCD",  # TODO: Should this be /1234-ABCD? The doc only mention rollups per item.
            "trailing_28_day_opens": "200",
            "trailing_28_day_impressions": "5000",
            "trailing_14_day_opens": "0",
            "trailing_14_day_impressions": "0",
            "trailing_7_day_opens": "0",
            "trailing_7_day_impressions": "0",
            "trailing_1_day_opens": "0",
            "trailing_1_day_impressions": "0",
            "created_at": "0",
            "expires_at": "0"
        })

        self.recommendationMetricsTable.put_item(Item={
            "recommendations_pk": "999999/1234-ABCD",
            "trailing_28_day_opens": "99",
            "trailing_28_day_impressions": "999",
            "trailing_14_day_opens": "0",
            "trailing_14_day_impressions": "0",
            "trailing_7_day_opens": "0",
            "trailing_7_day_impressions": "0",
            "trailing_1_day_opens": "0",
            "trailing_1_day_impressions": "0",
            "created_at": "0",
            "expires_at": "0"
        })

        self.recommendationMetricsTable.put_item(Item={
            "recommendations_pk": "666666/1234-ABCD",
            "trailing_28_day_opens": "66",
            "trailing_28_day_impressions": "999",
            "trailing_14_day_opens": "0",
            "trailing_14_day_impressions": "0",
            "trailing_7_day_opens": "0",
            "trailing_7_day_impressions": "0",
            "trailing_1_day_opens": "0",
            "trailing_1_day_impressions": "0",
            "created_at": "0",
            "expires_at": "0"
        })

        self.recommendationMetricsTable.put_item(Item={
            "recommendations_pk": "333333/1234-ABCD",
            "trailing_28_day_opens": "33",
            "trailing_28_day_impressions": "999",
            "trailing_14_day_opens": "0",
            "trailing_14_day_impressions": "0",
            "trailing_7_day_opens": "0",
            "trailing_7_day_impressions": "0",
            "trailing_1_day_opens": "0",
            "trailing_1_day_impressions": "0",
            "created_at": "0",
            "expires_at": "0"
        })
