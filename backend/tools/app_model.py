import json

from datetime import datetime
from django.db import models
from django.db.models.fields.related import RelatedField
from django.db.models.fields.reverse_related import ForeignObjectRel


class AppModel(models.Model):
    """Base class with common helpers for all models in the app."""

    class Meta:
        abstract = True

    def to_json_dict(self, field_names=None):
        fields = self.get_model_field_names() if field_names is None else field_names

        # TODO(Raj): HACK: Have separate json encoder for this.
        ret = {}
        for f in fields:
            val = getattr(self, f)
            try:
                json.dumps(val)
                ret[f] = val
            except TypeError:
                from decimal import Decimal

                if isinstance(val, Decimal):
                    ret[f] = float(val)

                elif isinstance(val, datetime):
                    ret[f] = val.isoformat()

                else:
                    ret[f] = str(val)

        return ret

    def get_model_field_names(self):
        ret = []
        for field in self._meta.get_fields():
            if isinstance(field, ForeignObjectRel):
                continue
            elif isinstance(field, RelatedField):
                ret.append(field.attname)
            else:
                ret.append(field.name)

        return ret


class TimeTrackedModel(AppModel):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta(AppModel.Meta):
        abstract = True
