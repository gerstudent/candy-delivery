from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import *
from .models import Courier


class RunValidationMixin:
    """
    Миксин для получения primary-key проблемной строки при валидации входных данных вместо ошибки
    """

    def run_validation(self, data):
        """
        Оверрайд дефолтного метода ради получения первичного ключа посылки с ошибкой, а не самой ошибки
        """
        try:
            valid = super().run_validation(data)
            return valid
        except ValidationError as e:
            # check if it's a list. This error is not linked to one piece of data.
            if data.__class__ is [].__class__:
                raise e
            primary_key_field_name = self.Meta.model._meta.pk.name
            raise ValidationError({"id": data[primary_key_field_name]})
            # "Entity {0} : {1}. Caused by : {2}".format(primary_key_field_name, data[primary_key_field_name],
            #                                            e.detail))


class CourierSerializer(serializers.ModelSerializer):
    rating = serializers.SerializerMethodField()
    earnings = serializers.SerializerMethodField()

    class Meta:
        model = Courier
        fields = '__all__'

    def get_rating(self, obj):
        rating = Courier.add_funcs.rating(obj.courier_id)
        return round(rating, 2) if isinstance(rating, float) else None

    def get_earnings(self, obj):
        return Courier.add_funcs.earnings(obj.courier_id)

    def to_representation(self, instance):
        """
        Удаляет пустые поля рейтинга и заработка
        """
        rep = super(serializers.ModelSerializer, self).to_representation(instance)

        if rep.get('rating') is None:
            rep.pop('rating')

        if rep.get('earnings') is None:
            rep.pop('earnings')

        return rep


class SingleCourierSerializer(RunValidationMixin, serializers.ModelSerializer):
    class Meta:
        model = Courier
        fields = '__all__'

    def validate(self, data):
        if not data.keys() == self.get_fields().keys():
            raise ValidationError("unexpected request fields")
        return data


class CourierPostSerializer(serializers.Serializer):
    data = SingleCourierSerializer(many=True)

    def create(self, validated_data):
        couriers = validated_data['data']
        for courier in couriers:
            Courier.objects.create(**courier)
        return validated_data


class OrderSerializer(RunValidationMixin, serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ("order_id", "weight", "region", "delivery_hours")


class OrderPostSerializer(serializers.Serializer):
    data = OrderSerializer(many=True)

    def create(self, validated_data):
        orders = validated_data['data']
        for order in orders:
            Order.objects.create(**order)
        return validated_data


class OrderIdSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ("order_id",)

    def to_representation(self, instance):
        prev = super().to_representation(instance)
        return {"id": prev.get("order_id")}


class BatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Batch
        fields = '__all__'
