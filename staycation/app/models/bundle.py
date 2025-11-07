from app import db
from datetime import datetime
from models.users import User
from models.package import Package

class BundledItem(db.EmbeddedDocument):
    # each selected package inside a bundle
    package = db.ReferenceField(Package, required=True)
    utilised = db.BooleanField(default=False)

class BundlePurchase(db.Document):
    meta = {'collection': 'bundlePurchases'}
    purchased_date = db.DateTimeField(default=datetime.utcnow)  # purchase time
    customer = db.ReferenceField(User, required=True)          # buyer
    bundledPackages = db.EmbeddedDocumentListField(BundledItem, default=[])

    @staticmethod
    def create_for_user(customer, package_objs):
        # persist a bundle with all selected packages marked unused
        items = [BundledItem(package=p, utilised=False) for p in package_objs]
        return BundlePurchase(customer=customer, bundledPackages=items).save()
