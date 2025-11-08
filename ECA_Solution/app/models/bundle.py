from app import db
from datetime import datetime, timedelta
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

    @property
    def expiry_date(self):
        # Bundle is valid for 1 year from purchase
        return self.purchased_date + timedelta(days=365)

    def is_expired(self):
        # True if bundle no longer valid
        return datetime.utcnow() > self.expiry_date

    @staticmethod
    def for_user_sorted(user):
        # All bundles for a user, ascending purchase date (requirement)
        return BundlePurchase.objects(customer=user).order_by('purchased_date')

    def mark_utilised(self, package_id):
        # Flip one bundled item to utilised = True
        for bi in self.bundledPackages:
            if str(bi.package.id) == str(package_id):
                bi.utilised = True
                self.save()
                return True
        return False

    def unutilised_items(self):
        # Convenience for templates
        return [bi for bi in self.bundledPackages if not bi.utilised]