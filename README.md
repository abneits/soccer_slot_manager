# 🏆 Indoor Football Reservation Platform

**A web application to manage weekly indoor football sessions, user
registrations, and player statistics.**

![License](https://img.shields.io/badge/License-MIT-blue.svg)
![Status](https://img.shields.io/badge/status-in%20development-yellow)
![MongoDB](https://img.shields.io/badge/Database-MongoDB-green)
![NodeJS](https://img.shields.io/badge/Backend-Node.js-brightgreen)
![React](https://img.shields.io/badge/Frontend-React-blue)

## 📖 Overview

Every Wednesday at **19:00**, the group has a one-hour indoor football
slot booked.\
This platform simplifies attendance management by allowing users to
register, invite guests, and track long-term performance.

## ✨ Features

### 🔐 User Management

-   Personal accounts with **email + password** authentication
-   Account creation requires **sponsorship** from an existing member
-   Only registered users can sign up for the next match
-   Users can add **unlimited guests** to each session
-   Registrations (personal or guests) can be **edited or removed** by
    their creator

### 🗄️ Database Structure (MongoDB)

#### `user` Collection

Each document contains:

``` json
{
  "firstName": "John",
  "lastName": "Doe",
  "displayName": "Johnny",
  "registrationDate": "2024-01-10T00:00:00Z"
}
```

#### `slot` Collection

Each document corresponds to a weekly session:

``` json
{
  "date": "2024-05-22T19:00:00Z",
  "registrations": [
    { "userId": "...", "guests": ["Friend A", "Friend B"] }
  ],
  "details": {
    "teams": {
      "teamA": [...],
      "teamB": [...]
    },
    "finalScore": "5–3"
  }
}
```

## 📅 Slot Management (Main Page)

The home screen provides: 
- Date of next Wednesday session
- List of registered players
- Index of added guests
- Team compositions (after game)
- Final match result

## 📊 Statistics

The platform automatically computes:

#### 🥇 Most Wins

Player with the highest number of match victories.

#### 📆 Best Attendance

Player who attended the most sessions.

#### 🤝 Top Contributor

User who invited or sponsored the most new participants.

## 📜 License

This project is licensed under the **MIT License**.
