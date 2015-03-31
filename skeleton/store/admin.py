{% if 'pages' in apps %}
from pages.admin import PageParentAdmin, PageAdminBase
from store.models import IndexPage, GenericPage


class IndexPageAdmin(PageAdminBase):
    base_model = IndexPage
    

PageParentAdmin.child_models += [
    (IndexPage, IndexPageAdmin)
]


class GenericPageAdmin(PageAdminBase):
    base_model = GenericPage


PageParentAdmin.child_models += [
    (GenericPage, GenericPageAdmin)
]

{% endif %}