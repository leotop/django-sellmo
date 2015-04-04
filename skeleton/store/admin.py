{% if 'pages' in apps %}
from pages.admin import PageParentAdmin, PageAdminBase
from pages.models import Page
from store.models import IndexPage, GenericPage


class IndexPageAdmin(PageAdminBase):
    base_model = Page
    

PageParentAdmin.child_models += [
    (IndexPage, IndexPageAdmin)
]


class GenericPageAdmin(PageAdminBase):
    base_model = Page


PageParentAdmin.child_models += [
    (GenericPage, GenericPageAdmin)
]

{% endif %}