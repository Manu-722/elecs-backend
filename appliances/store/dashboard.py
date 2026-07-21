from admin_tools.dashboard import modules, Dashboard

class CustomIndexDashboard(Dashboard):
    def init_with_context(self, context):
        self.children.append(modules.ModelList(
            title='Store Management',
            models=('store.models.Shoe', 'store.models.Order'),
        ))

        self.children.append(modules.LinkList(
            title='Quick Links',
            children=[
                {'title': 'View Transactions', 'url': '/admin/store/order/'},
                {'title': 'Manage Users', 'url': '/admin/auth/user/'},
            ]
        ))