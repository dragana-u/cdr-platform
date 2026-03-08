# ⚗️ Chemical Disposal Registry Platform

**Authors:**
- Iman Topchi (221008) — Faculty of Computer Science and Engineering, Ss. Cyril and Methodius University
- Dragana Usovikj (221043) — Faculty of Computer Science and Engineering, Ss. Cyril and Methodius University
- Novica Cvetkoski (221169) — Faculty of Computer Science and Engineering, Ss. Cyril and Methodius University

**Mentors:**
- **Dimitar Trajanov** — Faculty of Computer Science and Engineering, Ss. Cyril and Methodius University; Department of Computer Science, Metropolitan College, Boston University
- **Aleksandar Kondinski** — Institute of Physical and Theoretical Chemistry (PTC), Graz University of Technology (TU Graz)

## Prerequisites for running backend and frontend
> ⚠️ Some configurations, dependencies, and instructions will change as the project evolves.

Make sure you have the following installed before running the project:

- Java 17+ (preferably Java 25) 
- Maven
- Node.js (v22 recommended)
- Angular CLI
- PostgreSQL + pgAdmin

---

## Clone the Repository

**HTTPS:**
```bash
git clone https://github.com/dragana-u/cdr-platform.git
```

**SSH:**
```bash
git clone git@github.com:dragana-u/cdr-platform.git
```

## Database Setup

1. Open **pgAdmin**
2. Create a database and name it for example: ``cdrdbr``
3. Click **Save**

---

## Backend Setup (Spring Boot)

Open pom.xml in your preferred IDE 

Create your local `application.properties` file at `src/main/resources`:
```properties
server.port=8088
server.servlet.context-path=/rest

spring.datasource.url=jdbc:postgresql://localhost:5432/<your_db_name>
spring.datasource.username=<your_username>
spring.datasource.password=<your_passwor>

spring.jpa.hibernate.ddl-auto=update
spring.jpa.show-sql=true
spring.jpa.properties.hibernate.dialect=org.hibernate.dialect.PostgreSQLDialect
spring.jpa.properties.hibernate.format_sql=true
```

> ⚠️ Never commit your local application properties file.

Run the backend

The backend will be available at:
```
http://localhost:8088/rest
```

---

## Frontend Setup (Angular)

Open the frontend in your preferred IDE

Make sure the Node version is 20+

Install dependencies:
```bash
npm install
```

Run the frontend

The frontend will be available at:
```
http://localhost:4300
```
