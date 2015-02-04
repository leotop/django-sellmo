# Copyright (c) 2014, Adaptiv Design
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.

# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.

# 3. Neither the name of the copyright holder nor the names of its contributors
# may be used to endorse or promote products derived from this software without
# specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.


from sellmo import modules
from sellmo.api.decorators import load
from sellmo.api.product.models import (ProductRelatableManager,
                                       ProductRelatableQuerySet)
from sellmo.core.polymorphism import (PolymorphicModel,
                                      PolymorphicManager,
                                      PolymorphicQuerySet)
from sellmo.magic import ModelMixin

from django.db import models
from django.db.models.signals import (pre_save,
                                      post_save,
                                      pre_delete,
                                      m2m_changed)
from django.db.models import Q
from django.contrib.sites.models import Site
from django.utils.translation import ugettext_lazy as _


def on_discount_pre_save(sender, instance, **kwargs):
    if instance.pk is not None:
        old = instance.__class__.objects.get(pk=instance.pk)
        invalidate_indexes(discount=old)


def on_discount_post_save(sender, instance, **kwargs):
    invalidate_indexes(discount=instance)


def on_discount_m2m_changed(sender, instance, action, reverse, **kwargs):
    if action.startswith('post_'):
        if not reverse:
            invalidate_indexes(discount=instance)
        else:
            modules.pricing.get_index(
                'product_price').update(product=[instance])


def on_discount_pre_delete(sender, instance, **kwargs):
    invalidate_indexes(discount=instance)
        
        
def on_group_post_save(sender, instance, **kwargs):
    invalidate_indexes(group=instance)
    

def on_discount_groups_changed(sender, instance, **kwargs):
    invalidate_indexes(discount=instance)
    

def invalidate_indexes(discount=None, group=None):
    if discount:
        modules.pricing.get_index('product_price').update(
            product=modules.product.Product.objects.for_relatable(discount))
    elif group:
        modules.pricing.get_index('product_price').update(
            discount_group=[group])


@load(after='finalize_product_ProductRelatable')
@load(action='finalize_discount_Discount')
def finalize_model():

    class DiscountQuerySet(ProductRelatableQuerySet, PolymorphicQuerySet):
        pass

    class DiscountManager(ProductRelatableManager, PolymorphicManager):

        def get_by_natural_key(self, name):
            return self.get(name=name)

        def get_queryset(self):
            return DiscountQuerySet(self.model, using=self._db)

    class Discount(modules.discount.Discount, modules.product.ProductRelatable):

        objects = DiscountManager()
        
        if modules.discount.user_discount_enabled:
            groups = models.ManyToManyField(
                'discount.DiscountGroup',
                related_name='discounts',
                blank=True,
            )
        
        class Meta(
                modules.discount.Discount.Meta,
                modules.product.ProductRelatable.Meta):
            app_label = 'discount'

    modules.discount.Discount = Discount
    modules.discount.DiscountQuerySet = DiscountQuerySet
    modules.discount.DiscountManager = DiscountManager


class Discount(PolymorphicModel):

    name = models.CharField(
        max_length=80,
        verbose_name=_("name"),
        unique=True
    )
    
    products = models.ManyToManyField(
        'product.Product',
        related_name='discounts',
        blank=True,
    )

    def get_related_products_query(self):
        return super(Discount, self).get_related_products_query() | Q(discounts=self)

    def natural_key(self):
        return (self.name,)

    def apply(self, price):
        raise NotImplementedError()

    def __unicode__(self):
        return self.name

    class Meta:
        abstract = True
        verbose_name = _("discount")
        verbose_name_plural = _("discounts")


@load(action='finalize_discount_DiscountGroup')
def finalize_model():
    class DiscountGroup(modules.discount.DiscountGroup):
        
        class Meta(modules.discount.DiscountGroup.Meta):
            app_label = 'discount'
            
    modules.discount.DiscountGroup = DiscountGroup
    

@load(before='finalize_customer_Customer')
def load_model():
    class Customer(modules.customer.Customer):
        
        discount_group = models.ForeignKey(
            'discount.DiscountGroup',
            null=True,
            blank=True,
            verbose_name=_("discount group"),
        )
        
        class Meta(modules.customer.Customer.Meta):
            abstract = True

    modules.customer.Customer = Customer
        
        
class DiscountGroup(models.Model):
    
    name = models.CharField(
        max_length=80,
        verbose_name=_("name"),
        unique=True
    )
    
    def __unicode__(self):
        return self.name
        
    class Meta:
        abstract = True
        verbose_name = _("discount group")
        verbose_name_plural = _("discount groups")
    

def get_discount_groups():
    return [None] + list(modules.discount.DiscountGroup.objects.all())
   
     
@load(before='finalize_store_Purchase')
def load_model():
    if modules.discount.user_discount_enabled:
        class Purchase(modules.store.Purchase):
            
            def get_subtotal_kwargs(self):
                kwargs = super(Purchase, self).get_subtotal_kwargs()
                kwargs.update({
                    'discount_group': self.discount_group
                })
                return kwargs
            
            discount_group = models.ForeignKey(
                'discount.DiscountGroup',
                null=True,
                editable=False,
                on_delete=models.SET_NULL
            )
            
            class Meta(modules.store.Purchase.Meta):
                abstract = True
                
        modules.store.Purchase = Purchase
        

@load(after='finalize_product_Product')
def setup_indexes():
    if modules.discount.user_discount_enabled:
        index = modules.pricing.get_index('product_price')
        index.add_kwarg(
            'discount_group',
            models.ForeignKey(
                'discount.DiscountGroup',
                null=True),
            required=False,
            default=get_discount_groups,
        )


@load(after='finalize_discount_Discount')
@load(after='finalize_discount_DiscountGroup')
@load(after='discount_subtypes_registered')
def setup_discounts():
    for relation in modules.discount.Discount.m2m_invalidations:
        field = getattr(modules.discount.Discount, relation)
        m2m_changed.connect(on_discount_m2m_changed, sender=field.through)
    for subtype in modules.discount.subtypes:
        pre_save.connect(on_discount_pre_save, sender=subtype)
        post_save.connect(on_discount_post_save, sender=subtype)
        pre_delete.connect(on_discount_pre_delete, sender=subtype)

    if modules.discount.user_discount_enabled:
        m2m_changed.connect(
            on_discount_groups_changed,
            sender=modules.discount.Discount.groups.through)
        post_save.connect(
            on_group_post_save, sender=modules.discount.DiscountGroup)