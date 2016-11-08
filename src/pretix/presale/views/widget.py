from django.contrib.staticfiles import finders
from django.http import FileResponse, JsonResponse
from django.views import View

from pretix.presale.views.event import (
    get_grouped_items, item_group_by_category,
)


def widget_js(request, **kwargs):
    f = finders.find('pretixpresale/js/widget/widget.js')
    return FileResponse(open(f, 'rb'), content_type='text/javascript')


class WidgetAPIProductList(View):

    def get(self, request, **kwargs):
        data = {
            'currency': request.event.currency
        }

        items, display_add_to_cart = get_grouped_items(self.request.event)
        grps = []
        for cat, g in item_group_by_category(items):
            grps.append({
                'id': cat.pk if cat else None,
                'name': str(cat.name) if cat else None,
                'description': str(cat.description) if cat else None,
                'items': [
                    {
                        'id': item.pk,
                        'name': str(item.name),
                        'picture': item.picture.url if item.picture else None,
                        'description': str(item.description),
                        'has_variations': item.has_variations,
                        'require_voucher': item.require_voucher,
                        'order_max': item.order_max if not item.has_variations else None,
                        'price': item.price if not item.has_variations else None,
                        'min_price': item.min_price if item.has_variations else None,
                        'max_price': item.max_price if item.has_variations else None,
                        'tax_rate': item.tax_rate,
                        'avail': [
                            item.cached_availability[0],
                            item.cached_availability[1] if request.event.settings.show_quota_left else None
                        ] if not item.has_variations else None,
                        'variations': [
                            {
                                'id': var.id,
                                'value': str(var.value),
                                'order_max': var.order_max,
                                'price': var.price,
                                'avail': [
                                    var.cached_availability[0],
                                    var.cached_availability[1] if request.event.settings.show_quota_left else None
                                ] if not item.has_variations else None,
                            } for var in item.available_variations
                        ]

                    } for item in g
                ]
            })

        data['items_by_category'] = grps
        data['display_add_to_cart'] = display_add_to_cart

        vouchers_exist = self.request.event.get_cache().get('vouchers_exist')
        if vouchers_exist is None:
            vouchers_exist = self.request.event.vouchers.exists()
            self.request.event.get_cache().set('vouchers_exist', vouchers_exist)
        data['vouchers_exist'] = vouchers_exist

        resp = JsonResponse(data)
        resp['Access-Control-Allow-Origin'] = '*'
        return resp