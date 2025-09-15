#!/usr/bin/env python3
"""
Database setup script for Fantasy Recaps
This script helps initialize the Supabase database with the required schema.
"""

import os
import sys
import asyncio
from pathlib import Path
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


async def run_migration(supabase_url: str, supabase_service_key: str, migration_file: str):
    """Run a SQL migration file against the Supabase database"""
    
    # Create service role client
    supabase = create_client(supabase_url, supabase_service_key)
    
    # Read migration file
    migration_path = Path(__file__).parent / "migrations" / migration_file
    
    if not migration_path.exists():
        print(f"❌ Migration file not found: {migration_path}")
        return False
    
    print(f"📄 Reading migration: {migration_file}")
    
    with open(migration_path, 'r') as f:
        sql_content = f.read()
    
    # Split SQL into individual statements (basic splitting)
    statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
    
    print(f"🔄 Executing {len(statements)} SQL statements...")
    
    success_count = 0
    
    for i, statement in enumerate(statements, 1):
        # Skip comments and empty statements
        if statement.startswith('--') or not statement.strip():
            continue
        
        try:
            # Execute statement using Supabase RPC
            result = supabase.rpc('exec_sql', {'sql': statement}).execute()
            success_count += 1
            print(f"✅ Statement {i}/{len(statements)}: Success")
            
        except Exception as e:
            print(f"❌ Statement {i}/{len(statements)}: Failed - {str(e)}")
            # Continue with other statements
    
    print(f"\n📊 Migration Results:")
    print(f"   • Total statements: {len(statements)}")
    print(f"   • Successful: {success_count}")
    print(f"   • Failed: {len(statements) - success_count}")
    
    return success_count == len(statements)


async def setup_database():
    """Main database setup function"""
    
    print("🚀 Fantasy Recaps Database Setup")
    print("=" * 40)
    
    # Get environment variables
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    encryption_key = os.getenv('ENCRYPTION_KEY')
    
    if not supabase_url:
        print("❌ SUPABASE_URL environment variable is required")
        return False
    
    if not supabase_service_key:
        print("❌ SUPABASE_SERVICE_ROLE_KEY environment variable is required")
        return False
    
    if not encryption_key:
        print("⚠️  ENCRYPTION_KEY not set - API key encryption will not work")
    
    print(f"🔗 Connecting to Supabase: {supabase_url[:50]}...")
    
    try:
        # Test connection
        supabase = create_client(supabase_url, supabase_service_key)
        
        # Test basic query
        result = supabase.table('pg_tables').select('tablename').limit(1).execute()
        print("✅ Database connection successful")
        
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        return False
    
    # Run initial schema migration
    print("\n📋 Running initial schema migration...")
    success = await run_migration(supabase_url, supabase_service_key, "001_initial_schema.sql")
    
    if success:
        print("\n🎉 Database setup completed successfully!")
        print("\nNext steps:")
        print("1. Set up your fantasy platform API credentials")
        print("2. Configure LLM provider API keys")
        print("3. Start the backend server")
        return True
    else:
        print("\n❌ Database setup failed. Check the errors above.")
        return False


def print_usage():
    """Print usage instructions"""
    print("Usage: python setup_database.py")
    print("\nRequired environment variables:")
    print("  SUPABASE_URL             - Your Supabase project URL")
    print("  SUPABASE_SERVICE_ROLE_KEY - Your Supabase service role key")
    print("  ENCRYPTION_KEY           - Key for encrypting API keys (optional)")
    print("\nExample:")
    print("  export SUPABASE_URL='https://your-project.supabase.co'")
    print("  export SUPABASE_SERVICE_ROLE_KEY='your-service-role-key'")
    print("  export ENCRYPTION_KEY='your-encryption-key'")
    print("  python setup_database.py")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print_usage()
        sys.exit(0)
    
    # Run the setup
    success = asyncio.run(setup_database())
    sys.exit(0 if success else 1)
