import xmlrpc.client
import os
from typing import Optional, Dict, List, Any, cast

class OdooClient:
    def __init__(self):
        self.url = os.getenv('ODOO_URL')
        self.db = os.getenv('ODOO_DB')
        self.username = os.getenv('ODOO_USERNAME')
        self.password = os.getenv('ODOO_PASSWORD')
        self.uid: Optional[int] = None
        self.common: Optional[Any] = None
        self.models: Optional[Any] = None

    def authenticate(self) -> bool:
        try:
            self.common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
            self.models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')
            self.uid = self.common.authenticate(self.db, self.username, self.password, {})
            return self.uid is not None
        except Exception as e:
            print(f"Authentication failed: {e}")
            return False

    def execute(self, model: str, method: str, *args, **kwargs) -> Any:
        if not self.uid:
            if not self.authenticate():
                raise Exception("Failed to authenticate with Odoo")
        
        if self.models is None:
            raise Exception("Models proxy not initialized")
        
        return self.models.execute_kw(
            self.db, self.uid, self.password,
            model, method, list(args), kwargs
        )

    def search_read(self, model: str, domain: List, fields: List[str]) -> List[Dict]:
        if not self.uid:
            if not self.authenticate():
                raise Exception("Failed to authenticate with Odoo")
        
        if self.models is None:
            raise Exception("Models proxy not initialized")
        
        return self.models.execute_kw(
            self.db, self.uid, self.password,
            model, 'search_read',
            [domain],
            {'fields': fields}
        )

    def search_members_by_name(self, name: str) -> List[Dict]:
        domain = [('name', 'ilike', name)]
        fields = ['id', 'name', 'street', 'street2', 'city', 'zip', 'phone', 'mobile', 'email', 'image', 'image_small', 'image_medium']
        results = self.search_read('res.partner', domain, fields)
        print(f"Odoo search results for '{name}': {results}")
        return results
