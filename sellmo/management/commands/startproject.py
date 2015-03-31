from importlib import import_module

from optparse import make_option

from django.core.management.base import CommandError
from django.utils.crypto import get_random_string

from sellmo.management.template import TemplateCommand


DEFAULT_APPS = [
    'store',
    'product',
    'pricing',
    'category',
    'attribute',
    'variation',
    'cart',
    'checkout',
    'account',
    'settings',
    'mailing',
    'customer',
    'shipping',
    'payment',
    'tax',
    'discount',
    'availability',
    'brand',
    'color',
    'pages',
]


def handle_apps(apps):
    """
    Organizes multiple apps that are separated with commas or passed by
    using --apps/-a multiple times.
    For example: running 'sellmo-cli startproject -a store,product -a cart'
    would result in an app list: ['store', 'product', 'cart']
    >>> store(['store', 'store,product'', 'cart])
    {'store', 'product, 'cart}
    """
    app_list = []
    for app in apps:
        app_list.extend(app.replace(' ', '').split(','))
    return set(app_list)
    

class Command(TemplateCommand):
    help = ("Creates a Django Sellmo project directory structure for the given "
            "project name in the current directory or optionally in the "
            "given directory.")

    option_list = TemplateCommand.option_list + (
        make_option('--apps', '-a',
            dest='apps',
            action='append', default=DEFAULT_APPS,
            help='Sellmo apps to create (default: "{default}"). '
                 'Separate multiple apps with commas, or use '
                 '-a multiple times.'.format(default=','.join(DEFAULT_APPS))),
    )
    
    def handle(self, project_name=None, target=None, *args, **options):
        
        self.validate_name(project_name, "project")
        
        # Check that the project_name cannot be imported.
        try:
            import_module(project_name)
        except ImportError:
            pass
        else:
            raise CommandError("%r conflicts with the name of an existing "
                               "Python module and cannot be used as a "
                               "project name. Please try another name." %
                               project_name)

        # Create a random SECRET_KEY hash to put it in the main settings.
        chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
        options['secret_key'] = get_random_string(50, chars)
        
        # Collect sellmo apps
        apps = tuple(handle_apps(options.pop('apps')))
        
        super(Command, self).handle('project', project_name, target, apps=apps, **options)
        self.stdout.write("\nNow run: python manage.py makemigrations %s\n" % ' '.join(apps))
        
    def preprocess_file(self, filename, context):
        # First make sure this app should be generated
        app = context.get('app', None)
        if app is not None and app not in context.get('apps'):
            return False