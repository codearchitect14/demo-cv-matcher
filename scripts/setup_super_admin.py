"""
Script to create/update Super Admin account
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

async def create_super_admin():
    """Create super admin account"""
    from config.connection_pool import global_pool
    from config.security import get_password_hash
    
    # Super admin details
    email = "aliboolmind228@gmail.com"
    full_name = "Ali Mughal"
    password = "SuperAdmin@123"  # Change this to your desired password
    
    print("=" * 60)
    print("Super Admin Setup")
    print("=" * 60)
    print()
    
    try:
        # Check if super admin already exists
        existing = await global_pool.fetchrow(
            "SELECT id, email, full_name FROM super_admins WHERE email = $1",
            email
        )
        
        if existing:
            print(f"Super admin already exists with email: {email}")
            print(f"   ID: {existing['id']}")
            print(f"   Name: {existing['full_name']}")
            print()
            
            # Update password
            response = input("Do you want to update the password? (yes/no): ")
            if response.lower() == 'yes':
                new_password = input("Enter new password: ")
                if new_password:
                    hashed_password = get_password_hash(new_password)
                    await global_pool.execute(
                        """
                        UPDATE super_admins 
                        SET password_hash = $1, updated_at = NOW()
                        WHERE email = $2
                        """,
                        hashed_password, email
                    )
                    print(f"Password updated for {email}")
                else:
                    print(" Password cannot be empty")
            else:
                print(" No changes made")
        else:
            # Create new super admin
            hashed_password = get_password_hash(password)
            
            result = await global_pool.fetchrow(
                """
                INSERT INTO super_admins (email, password_hash, full_name, is_active, created_at, updated_at)
                VALUES ($1, $2, $3, true, NOW(), NOW())
                RETURNING id, email, full_name
                """,
                email, hashed_password, full_name
            )
            
            print(f" Super admin created successfully!")
            print(f"   ID: {result['id']}")
            print(f"   Email: {result['email']}")
            print(f"   Name: {result['full_name']}")
            print(f"   Password: {password}")
            print()
            print(f"  IMPORTANT: Change the password after first login!")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Update .env file with: SUPER_ADMIN_EMAIL=aliboolmind228@gmail.com")
    print("2. Restart your backend server")
    print("3. Login at: http://localhost:3000/super-admin/login")
    print(f"4. Use email: {email}")
    print(f"5. Use password: {password}")
    print()
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(create_super_admin())

