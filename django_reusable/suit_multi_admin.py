def suit_multi_admin():
    """Monkeypatch Django Suit to support multiple Admin Sites

    Usage:

        put this code for example in myapp/monkey.py

        Activate the monkeypatch in your models.py:

        from monkey import suit_multi_admin
        suit_multi_admin()

        Put a separate configuration in your settings as:
        SUIT_CONFIG_<MYADMIN> = {...}
        where MYADMIN is the upper case name of your custom AdminSite.name

    """

    import suit.config
    from suit.templatetags import suit_menu
    from django.conf import settings
    from django.core.handlers.wsgi import WSGIRequest

    def get_config(param=None, config_key='SUIT_CONFIG'):
        """
        Accept a custom config_key kwarg
        """
        if hasattr(settings, config_key):
            config = getattr(settings, config_key, {})
        else:
            config = suit.config.default_config()
        if param:
            value = config.get(param)
            if value is None:
                value = suit.config.default_config().get(param)
            return value
        return config

    suit.config.get_config = get_config

    @suit_menu.register.simple_tag(takes_context=True)
    def get_menu(context, request):
        """
        Pass admin_site_name go Menu via context
        """
        if not isinstance(request, WSGIRequest) or request.user.is_anonymous:
            return None

        # Try to get app list
        if hasattr(request, 'current_app'):
            # Django 1.8 uses request.current_app instead of context.current_app
            admin_site = suit_menu.get_admin_site(request.current_app)
        else:
            try:
                admin_site = suit_menu.get_admin_site(context.current_app)
            # Django 1.10 removed the current_app parameter for some classes and functions.
            # Check the release notes.
            except AttributeError:
                admin_site = suit_menu.get_admin_site(context.request.resolver_match.namespace)

        # Try to get app list
        template_response = admin_site.index(request)
        context['admin_site_name'] = admin_site.name
        try:
            app_list = template_response.context_data['app_list']
        except Exception:
            return
        menu = suit_menu.Menu(context, request, app_list)
        menu_app_list = [app for app in menu.get_app_list() if app.get('models') or app.get('url')]
        if menu.conf_menu_extras:
            menu_app_list.extend(menu.make_menu(menu.conf_menu_extras))
        if getattr(settings, 'REUSABLE_SHOW_ERRORS_LINK', False):
            menu_app_list.extend(menu.make_menu((
                {
                    'label': 'Errors',
                    'url': 'django_reusable:errors',
                    'permissions': getattr(settings, 'REUSABLE_SHOW_ERRORS_PERM', 'django_reusable.view_errors')
                },
            )))
        return menu_app_list

    suit_menu.get_menu = get_menu

    def patched_init(self, context, request, app_list):
        """
        Get admin_site_name from context
        """
        self.request = request
        self.app_list = app_list
        self.admin_site_name = context.get('admin_site_name')

        # Detect current app, if any
        try:
            self.ctx_app = context['app_label'].lower()
        except Exception:
            self.ctx_app = None

        # Get current model plural name, if any
        try:
            self.ctx_model_plural = context['opts'].verbose_name_plural.lower()
        except Exception:
            self.ctx_model_plural = None

        # Flatten all models from native apps
        self.all_models = [model for app in app_list for model in app['models']]

        # Init config variables
        self.init_config()
        super(suit_menu.Menu, self).__init__()

    suit_menu.Menu.__init__ = patched_init

    def patched_init_config(self):
        """
        Set config_key based on admin_site_name.
        """
        if self.admin_site_name and self.admin_site_name != 'admin':
            config_key = 'SUIT_CONFIG_{}'.format(self.admin_site_name.upper())
        else:
            config_key = 'SUIT_CONFIG'
        self.conf_exclude = get_config('MENU_EXCLUDE', config_key)
        self.conf_open_first_child = get_config('MENU_OPEN_FIRST_CHILD', config_key)
        self.conf_icons = get_config('MENU_ICONS', config_key)
        self.conf_menu_order = get_config('MENU_ORDER', config_key)
        self.conf_menu = get_config('MENU', config_key)
        self.conf_menu_extras = get_config('MENU_EXTRAS', config_key)

    suit_menu.Menu.init_config = patched_init_config

    original_app_is_forbidden = suit_menu.Menu.app_is_forbidden

    def patched_is_forbidden(self, entity):
        if entity['permissions'] and callable(entity['permissions']):
            return not entity['permissions'](self.request.user)
        return original_app_is_forbidden(self, entity)

    suit_menu.Menu.app_is_forbidden = patched_is_forbidden
    suit_menu.Menu.model_is_forbidden = patched_is_forbidden
