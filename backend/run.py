from app import create_app

app = create_app()

if __name__ == '__main__':
    print("🚀 Starting CommunitySkillShare API...")
    print("📍 Access your API at: http://localhost:5000")
    print("📚 API Documentation: http://localhost:5000/")
    app.run(debug=True, host='0.0.0.0', port=5000)