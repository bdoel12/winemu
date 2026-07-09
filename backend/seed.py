"""
Seed script for Winemu database.
Run: python seed.py
"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from app.extensions import db
from app.models import User, Category


def seed():
    app = create_app()
    with app.app_context():
        # Categories
        categories = [
            {'name': 'Elektronik', 'slug': 'elektronik', 'icon': 'devices'},
            {'name': 'Dokumen', 'slug': 'dokumen', 'icon': 'description'},
            {'name': 'Dompet & Uang', 'slug': 'dompet-uang', 'icon': 'wallet'},
            {'name': 'Kunci & Akses', 'slug': 'kunci-akses', 'icon': 'key'},
            {'name': 'Tas & Ransel', 'slug': 'tas-ransel', 'icon': 'backpack'},
            {'name': 'Perhiasan', 'slug': 'perhiasan', 'icon': 'diamond'},
            {'name': 'Kendaraan', 'slug': 'kendaraan', 'icon': 'directions_car'},
            {'name': 'Hewan Peliharaan', 'slug': 'hewan-peliharaan', 'icon': 'pets'},
            {'name': 'Pakaian', 'slug': 'pakaian', 'icon': 'checkroom'},
            {'name': 'Lainnya', 'slug': 'lainnya', 'icon': 'category'},
        ]
        for c in categories:
            if not Category.query.filter_by(slug=c['slug']).first():
                cat = Category(**c)
                db.session.add(cat)

        # Admin user
        if not User.query.filter_by(email='admin@winemu.id').first():
            admin = User(
                username='admin',
                email='admin@winemu.id',
                full_name='Admin Winemu',
                role='admin',
                is_active=True,
                is_verified=True,
            )
            admin.set_password('admin123')
            db.session.add(admin)

        # Demo user
        if not User.query.filter_by(email='demo@winemu.id').first():
            demo = User(
                username='demo_user',
                email='demo@winemu.id',
                full_name='Budi Santoso',
                bio='Pecinta kopi dan pencari barang hilang di Yogyakarta.',
                location='Yogyakarta',
                role='user',
                is_active=True,
                is_verified=True,
            )
            demo.set_password('demo123')
            db.session.add(demo)

        db.session.commit()
        print("✅ Database seeded successfully!")
        print("   Admin: admin@winemu.id / admin123")
        print("   Demo:  demo@winemu.id / demo123")


if __name__ == '__main__':
    seed()
