# Billing App Deployment Guide

## 🚀 Frontend Deployment (Vercel)

### 1. Prepare for Deployment
- Remove or ignore `firebase.js` file
- Ensure all Firebase imports are removed from components
- Test locally with your Flask backend

### 2. Deploy to Vercel
1. **Push code to GitHub**
2. **Go to [Vercel](https://vercel.com)**
3. **Import your GitHub repository**
4. **Set environment variables:**
   ```
   REACT_APP_API_URL=https://your-backend-url.com
   ```
5. **Deploy!**

## 🔧 Backend Deployment (Railway/Render)

### Option 1: Railway (Recommended)
1. **Go to [Railway](https://railway.app)**
2. **Connect your GitHub account**
3. **Create new project from GitHub**
4. **Set environment variables:**
   ```
   FLASK_ENV=production
   SECRET_KEY=your-super-secret-key-here
   DB_HOST=your-mysql-host
   DB_USER=your-mysql-user
   DB_PASSWORD=your-mysql-password
   DB_NAME=your-mysql-database
   ```
5. **Deploy!**

### Option 2: Render
1. **Go to [Render](https://render.com)**
2. **Create new Web Service**
3. **Connect your GitHub repository**
4. **Set environment variables (same as above)**
5. **Deploy!**

## 🗄️ Database Options

### Option 1: Railway MySQL
- Railway provides managed MySQL databases
- Easy to set up and manage
- Automatic backups

### Option 2: PlanetScale
- Serverless MySQL platform
- Great for production apps
- Free tier available

### Option 3: AWS RDS
- Enterprise-grade MySQL
- More complex setup
- Highly reliable

## 🔒 Security Checklist

- [ ] Change default SECRET_KEY
- [ ] Use HTTPS in production
- [ ] Set secure session cookies
- [ ] Use environment variables for sensitive data
- [ ] Enable CORS only for your frontend domain

## 📱 Testing After Deployment

1. **Test signup** - Create a new account
2. **Test login** - Sign in with credentials
3. **Test authentication** - Check if sessions work
4. **Test billing operations** - Add/edit/delete bills

## 🆘 Troubleshooting

### Common Issues:
- **CORS errors**: Check CORS configuration
- **Database connection**: Verify environment variables
- **Session issues**: Check SECRET_KEY and cookie settings
- **Build errors**: Ensure all dependencies are in requirements.txt

## 🎯 Next Steps

1. **Deploy backend first**
2. **Test backend endpoints**
3. **Deploy frontend with correct API URL**
4. **Test full application**
5. **Set up monitoring and logging**




