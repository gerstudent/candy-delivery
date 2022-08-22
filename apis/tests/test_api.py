import datetime
import json

from django.test import Client, TestCase


class ApiInputTests(TestCase):
    def test_setUp(self):
        self.client = Client()

    def test_postCourierCorrect(self):
        data = {
            "data": [
                {
                    "courier_id": 1,
                    "courier_type": "foot",
                    "regions": [1, 12, 22],
                    "working_hours": ["11:35-14:05", "09:00-11:00"]
                },
                {
                    "courier_id": 2,
                    "courier_type": "bike",
                    "regions": [22],
                    "working_hours": ["09:00-18:00"]
                },
                {
                    "courier_id": 3,
                    "courier_type": "car",
                    "regions": [12, 22, 23, 33],
                    "working_hours": ["08:00-12:00"]
                },
                {
                    "courier_id": 4,
                    "courier_type": "car",
                    "regions": [14],
                    "working_hours": ["08:00-12:00"]
                },
            ]
        }

        correct_response = {"couriers": [{"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}]}

        response = self.client.post(path='/couriers',
                                    data=data,
                                    content_type="application/json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(json.loads(response.content), correct_response)

    def test_postCourierBad(self):
        """
        Проверка на пропущенные, неописанные и невалидные поля
        """

        data = {
            "data": [
                {
                    "courier_id": 4,
                    "courier_type": "foot",
                    "regions": [1, 12, 22],
                    "working_hours": ["11:35-14:05", "09:00-11:00"],
                    "someField": "someValue"
                },
                {
                    "courier_id": 5,
                    "courier_type": "bike",
                    "working_hours": ["09:00-18:00"]
                },
                {
                    "courier_id": 6,
                    "courier_type": "car",
                    "regions": [12, 22, 23, 33],
                    "working_hours": ["10:00-12:00"]
                },
                {
                    "courier_id": 7,
                    "courier_type": "car",
                    "regions": [12, 22, 23, 33, "12d"],
                    "working_hours": ["10:00-12:00"]
                },
            ]
        }

        correct_response = {
            "validation_error": {
                "couriers": [{"id": 4}, {"id": 5}, {"id": 7}]
            }
        }

        response = self.client.post(path='/couriers',
                                    data=data,
                                    content_type="application/json")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.content), correct_response)

    def test_patchCouriers_correct(self):
        self.test_postCourierCorrect()

        data = {
            "regions": [11, 33, 2]
        }

        correct_response = {
            "courier_id": 2,
            "courier_type": "bike",
            "regions": [11, 33, 2],
            "working_hours": ["09:00-18:00"]
        }

        response = self.client.patch(path='/couriers/2',
                                     data=data,
                                     content_type="application/json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), correct_response)

    def test_patchCouriers_badrequest(self):
        data = {
            "SomeField": [11, 33, 2]
        }

        response = self.client.patch(path='/couriers/2',
                                     data=data,
                                     content_type="application/json")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, b'')

    def test_postOrders_correct(self):
        data = {
            "data": [
                {"order_id": 1, "weight": 0.14, "region": 12, "delivery_hours": ["09:00-18:00"]},
                {"order_id": 2, "weight": 50, "region": 1, "delivery_hours": ["09:00-18:00"]},
                {"order_id": 3, "weight": 0.02, "region": 22, "delivery_hours": ["09:00-12:00", "16:00-21:30"]},
                {"order_id": 10, "weight": 3.7, "region": 33, "delivery_hours": ["07:00-09:00"]},
                {"order_id": 11, "weight": 2.3, "region": 33, "delivery_hours": ["07:00-09:00"]},
                {"order_id": 12, "weight": 1.4, "region": 45, "delivery_hours": ["07:00-09:00"]},
                {"order_id": 14, "weight": 49, "region": 33, "delivery_hours": ["07:00-09:00"]},
            ]
        }

        correct_response = {
            "orders": [{"id": 1}, {"id": 2}, {"id": 3}, {"id": 10}, {"id": 11}, {"id": 12}, {"id": 14}]
        }

        response = self.client.post(path='/orders',
                                    data=data,
                                    content_type="application/json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(json.loads(response.content), correct_response)

    def test_postOrders_minvalue(self):
        data = {
            "data": [
                {"order_id": 234, "weight": 0.01, "region": 12, "delivery_hours": ["09:00-18:00"]},
               ]
        }

        correct_response = {
            "orders": [{"id": 234},]
        }

        response = self.client.post(path='/orders',
                                    data=data,
                                    content_type="application/json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(json.loads(response.content), correct_response)

    def test_postOrderBad(self):
        data = {
            "data": [
                {
                    "order_id": 4,
                    "weight": 0.23,
                    "region": 12,
                },
                {
                    "order_id": 5,
                    "weight": 51,
                    "region": 1,
                    "delivery_hours": ["09:00-18:00"]
                },
                {
                    "order_id": 6,
                    "weight": 12,
                    "region": 1,
                    "delivery_hours": [3]
                },
                {
                    "order_id": 112,
                    "weight": 0.005,
                    "region": 1,
                    "delivery_hours": ["08:00-19:00"]
                },
            ]
        }

        correct_response = {
            "validation_error": {
                "orders": [{"id": 4}, {"id": 5}, {"id": 112}]
            }
        }

        response = self.client.post(path='/orders',
                                    data=data,
                                    content_type="application/json")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.content), correct_response)

    def test_assignOrder(self):
        """
        Проверка на вес, регионы и время при существовании подходящих заказов
        """

        self.test_postCourierCorrect()
        self.test_postOrders_correct()

        data = {
            "courier_id": 3
        }

        response = self.client.post(path='/orders/assign',
                                    data=data,
                                    content_type="application/json")

        correct_response = {
            "orders": [{"id": 1}, {"id": 3}, {"id": 10}, {"id": 11}]
        }

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)["orders"], correct_response["orders"])

    def test_assignOrder_empty(self):
        """
        Тест при отсутствии подходящих заказов
        """

        self.test_postCourierCorrect()
        self.test_postOrders_correct()

        data = {
            "courier_id": 4
        }

        response = self.client.post(path='/orders/assign',
                                    data=data,
                                    content_type="application/json")

        correct_response = {
            "orders": []
        }

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), correct_response)

    def test_noCourier(self):
        """
        HTTP 400
        """

        self.test_postCourierCorrect()
        self.test_postOrders_correct()

        data = {
            "courier_id": 98
        }

        response = self.client.post(path='/orders/assign',
                                    data=data,
                                    content_type="application/json")

        self.assertEqual(response.status_code, 400)

    def test_complete_order(self):

        self.test_assignOrder()

        data = {
            "courier_id": 3,
            "order_id": 3,
            "complete_time": datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-4] + "Z"
        }

        response = self.client.post(path='/orders/complete',
                                    data=data,
                                    content_type="application/json")

        correct_response = {
            "order_id": 3
        }

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), correct_response)

    def test_wrongCourier(self):
        """
        Курьер не соответствует заказу
        """

        self.test_assignOrder()

        data = {
            "courier_id": 4,
            "order_id": 3,
            "complete_time": datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-4] + "Z"
        }

        response = self.client.post(path='/orders/complete',
                                    data=data,
                                    content_type="application/json")

        self.assertEqual(response.status_code, 400)


class CheckAfterAssignTests(TestCase):
    fixtures = ["assign_data.json"]

    def test_setUp(self):
        self.Client = Client()

    def test_patch_incompatible_orders(self):

        patch_data = {
            "regions": [1, 2]
        }

        assign_data = {
            "courier_id": 1,
        }

        correct_response_patch = {
            "courier_id": 1,
            "courier_type": "foot",
            "regions": [1, 2],
            "working_hours": ["08:00-12:00"]
        }

        correct_response_assign = {
            "orders":
                [
                    {"id": 5},
                ],
        }

        response_patch = self.client.patch(path='/couriers/1',
                                           data=patch_data,
                                           content_type="application/json")

        response_assign = self.client.post(path='/orders/assign',
                                           data=assign_data,
                                           content_type="application/json")

        self.assertEqual(response_patch.status_code, 200)
        self.assertEqual(json.loads(response_patch.content), correct_response_patch)

        self.assertEqual(response_assign.status_code, 200)
        self.assertEqual(json.loads(response_assign.content)["orders"], correct_response_assign["orders"])


class CalculationTests(TestCase):
    fixtures = ["courier_get_test_data.json"]

    def test_setUp(self):
        self.Client = Client()

    def test_infoCorrect(self):
        response = self.client.get(path='/couriers/1')

        correct_response = {
            "courier_id": 1,
            "courier_type": "foot",
            "regions": [1, 2, 3],
            "working_hours": ["08:00-12:00"],
            "rating": 4.89,
            "earnings": 1000,
        }

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), correct_response)

    def test_noRating(self):
        """
        Курьер без выполненных развозов
        """
        response = self.client.get(path='/couriers/2')

        correct_response = {
            "courier_id": 2,
            "courier_type": "bike",
            "regions": [4],
            "working_hours": ["12:00-13:00"],
            "earnings": 0,
        }

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), correct_response)

    def test_getInfo_no_courier(self):
        """
        Невалидный id курьера
        """

        response = self.client.get(path='/couriers/17')

        self.assertEqual(response.status_code, 404)
