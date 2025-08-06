import asyncio
from sqlalchemy import text
from config.database import AsyncSessionLocal

async def fix_enum_values():
    async with AsyncSessionLocal() as session:
        try:
            print("Current enum values in database:")
            
            result = await session.execute(text("SELECT unnest(enum_range(NULL::companysize)) as company_size_values;"))
            company_sizes = result.fetchall()
            print("Company size enum values:")
            for row in company_sizes:
                print(f"  - {row[0]}")
            
            result = await session.execute(text("SELECT unnest(enum_range(NULL::domain)) as domain_values;"))
            domains = result.fetchall()
            print("Domain enum values:")
            for row in domains:
                print(f"  - {row[0]}")
            
            print("\nThe issue is that the database has enum NAMES but the frontend sends enum VALUES.")
            print("We need to recreate the enum types with the correct values.")
            
            # Drop and recreate the enum types with correct values
            print("\nRecreating enum types with correct values...")
            
            # Drop existing enum types (this will fail if they're in use, but that's okay)
            try:
                await session.execute(text("DROP TYPE IF EXISTS companysize CASCADE"))
                await session.execute(text("DROP TYPE IF EXISTS domain CASCADE"))
                print("Dropped existing enum types")
            except Exception as e:
                print(f"Note: Could not drop enum types (they may be in use): {e}")
            
            # Create new enum types with correct values
            await session.execute(text("""
                CREATE TYPE companysize AS ENUM (
                    '1-10', '11-50', '51-200', '201-500', '501-1000', '1000+'
                )
            """))
            print("Created companysize enum with correct values")
            
            await session.execute(text("""
                CREATE TYPE domain AS ENUM (
                    'IT', 'Healthcare', 'Finance', 'Education', 'Manufacturing', 
                    'Retail', 'Consulting', 'Media', 'Real Estate', 'Transportation', 
                    'Energy', 'Telecommunications', 'Other'
                )
            """))
            print("Created domain enum with correct values")
            
            await session.commit()
            print("\nEnum types recreated successfully!")
            
            # Show the updated enum values
            print("\nUpdated enum values:")
            result = await session.execute(text("SELECT unnest(enum_range(NULL::companysize)) as company_size_values;"))
            company_sizes = result.fetchall()
            print("Company size enum values:")
            for row in company_sizes:
                print(f"  - {row[0]}")
            
            result = await session.execute(text("SELECT unnest(enum_range(NULL::domain)) as domain_values;"))
            domains = result.fetchall()
            print("Domain enum values:")
            for row in domains:
                print(f"  - {row[0]}")
                
        except Exception as e:
            print(f"Error fixing enum values: {e}")
            await session.rollback()

if __name__ == "__main__":
    asyncio.run(fix_enum_values()) 