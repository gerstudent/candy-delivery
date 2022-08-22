import itertools
import time

from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import connection
from django.db import models
from django.db.models import Sum, Window, F


def timecheck(a, b):
    l1, h1 = time.strptime(a[:5], "%H:%M"), time.strptime(a[6:], "%H:%M")
    l2, h2 = time.strptime(b[:5], "%H:%M"), time.strptime(b[6:], "%H:%M")
    return l1 < h2 and h1 > l2


def select_orders_by_time(work, delivery):
    return any([timecheck(*pair) for pair in itertools.product(work, delivery)])


class OrderManager(models.Manager):
    max_weight = {'foot': 10,
                  'bike': 15,
                  'car': 50}

    def check_batches(self, **kwargs):
        try:
            batch = Batch.objects.get(**kwargs)
        except Batch.DoesNotExist:
            batch = None
        return batch

    def check_after_update(self, courier):
        batch = self.check_batches(courier_id=courier.courier_id, is_complete=False)
        if batch:
            orders = Order.objects.filter(batch_id=batch.batch_id, region__in=courier.regions)
            orders = [order.order_id for order in orders if
                      select_orders_by_time(courier.working_hours, order.delivery_hours)]
            weighted = Order.objects.filter(order_id__in=orders).annotate(sum_weight=Window(expression=Sum('weight'),
                                                                                            order_by=F("weight").asc()))
            good_orders = [i.order_id for i in weighted if i.sum_weight <= self.max_weight.get(courier.courier_type)]

            Order.objects.filter(batch_id=batch.batch_id) \
                .exclude(order_id__in=good_orders) \
                .update(batch_id=None)

            # deletes batch if all orders from it are deleted
            if not Order.objects.filter(batch_id=batch.batch_id).exists():
                batch.delete()

    def assign_order(self, courier_id):
        try:
            courier = Courier.objects.get(pk=courier_id)
        except:
            return None
        batch = self.check_batches(courier_id=courier.courier_id, is_complete=False)
        if batch:
            orders = Order.objects.filter(batch_id=batch.batch_id, complete_time__isnull=True)
            return orders, batch.assign_time
        else:
            try:
                orders = Order.objects.filter(region__in=courier.regions, batch_id__isnull=True) \
                    .order_by("weight")
            except:
                return []

            orders = [order.order_id for order in orders if
                      select_orders_by_time(courier.working_hours, order.delivery_hours)]

            if not orders:
                return []

            weighted = Order.objects.filter(order_id__in=orders).annotate(sum_weight=Window(expression=Sum('weight'),
                                                                                            order_by=F("weight").asc()))
            correct_ids = [i.order_id for i in weighted if i.sum_weight <= self.max_weight.get(courier.courier_type)]

            good = Order.objects.filter(pk__in=correct_ids)
            batch = Batch.objects.create(courier_id=courier.courier_id,
                                         courier_type=courier.courier_type)
            good.update(batch_id=batch.batch_id)
            return good, batch.assign_time

    def complete_order(self, data):
        try:
            order = Order.objects.select_related().get(pk=data.get("order_id"),
                                                       batch__courier_id=data.get("courier_id"))
        except:
            return None
        order.complete_time = data.get("complete_time")
        order.save(update_fields=['complete_time'])
        if not Order.objects.filter(batch_id=order.batch.batch_id, complete_time__isnull=True):
            order.batch.is_complete = True
            order.batch.save(update_fields=['is_complete'])
        return order


class CourierManager(models.Manager):
    def rating(self, courier_id):
        """
        Эффективный запрос на получение рейтинга, быстрее и проще, чем ORM от Django
        """
        query = """SELECT MIN(region_avg) FROM
                    (SELECT AVG(extract(epoch from (finish::timestamp - start::timestamp))) as region_avg FROM
                    (SELECT region, complete_time as finish,
                           CASE
                            WHEN row_number() OVER(PARTITION BY region ORDER BY complete_time ASC) = 1 THEN assign_time
                            ELSE LAG(complete_time) OVER(PARTITION BY region ORDER BY complete_time ASC)
                            END
                            AS start
                    FROM apis_order LEFT JOIN apis_batch ab on apis_order.batch_id = ab.batch_id
                    WHERE ab.is_complete = True AND courier_id = %s) as sub
                    GROUP BY region) as mins;"""
        with connection.cursor() as cursor:
            cursor.execute(query, [courier_id])
            t = cursor.fetchone()[0]
        return (60 * 60 - min(t, 60 * 60)) / (60 * 60) * 5 if t else None

    def earnings(self, courier_id):
        coefs = {'foot': 2,
                 'bike': 5,
                 'car': 9}

        batches = Batch.objects.filter(courier_id=courier_id, is_complete=True)
        return 500 * sum([coefs.get(key) for key in batches.values_list("courier_type", flat=True)])


class Courier(models.Model):
    COURIER_TYPE_CHOICES = (
        ("foot", "foot"),
        ("bike", "bike"),
        ("car", "car"),
    )

    courier_id = models.PositiveIntegerField(primary_key=True, blank=False)
    courier_type = models.CharField(max_length=4, choices=COURIER_TYPE_CHOICES, blank=False)
    regions = ArrayField(base_field=models.IntegerField(null=False, blank=False), blank=False)
    working_hours = ArrayField(base_field=models.CharField(max_length=15), blank=False)

    add_funcs = CourierManager()
    objects = models.Manager()


class Batch(models.Model):
    COURIER_TYPE_CHOICES = (
        ("foot", "foot"),
        ("bike", "bike"),
        ("car", "car"),
    )
    batch_id = models.AutoField(primary_key=True)
    assign_time = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    is_complete = models.BooleanField(default=False)
    courier = models.ForeignKey(Courier, on_delete=models.CASCADE, blank=True, null=True)
    courier_type = models.CharField(max_length=4, choices=COURIER_TYPE_CHOICES, blank=True, null=True)


class Order(models.Model):
    order_id = models.PositiveIntegerField(primary_key=True, blank=False)
    weight = models.DecimalField(max_digits=4, decimal_places=2,
                                 validators=[MinValueValidator(0), MaxValueValidator(50)],
                                 blank=False)
    region = models.PositiveIntegerField(blank=False)
    delivery_hours = ArrayField(base_field=models.CharField(max_length=15), blank=False)
    complete_time = models.DateTimeField(auto_now=False, blank=True, null=True)
    batch = models.ForeignKey(Batch, on_delete=models.PROTECT, blank=True, null=True)

    objects = models.Manager()
    order_manager = OrderManager()
