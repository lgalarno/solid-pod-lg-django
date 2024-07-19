require('dotenv').config()

const cors = require('cors');
const express = require('express');
const bodyParser = require('body-parser');
const cookieSession = require("cookie-session");
const fileUpload = require('express-fileupload');

// const session = require('express-session')

const PORT = process.env.PORT || 3030;
const HOST = process.env.HOST || 'localhost';
const app = express();

const authRouter = require('./routes/auth')
const resourcesRouter = require('./routes/resources')
const adminRouter = require('./routes/admin')
// const solidPodLghRouter = require('./routes/solid-pod-lg')

// The following snippet ensures that the server identifies each user's session
// with a cookie using an express-specific mechanism
app.use(fileUpload());
app.use(cors());
app.use(bodyParser.urlencoded({ 
  parameterLimit: 100000,
  limit: '100mb',
  extended: true }));
app.use(bodyParser.json());
// The following snippet ensures that the server identifies each user's session
// with a cookie using an express-specific mechanism
app.use(
    cookieSession({
        name: "session",
        // These keys are required by cookie-session to sign the cookies.
        keys: [
        "Required, but value not relevant for this demo - key1",
        "Required, but value not relevant for this demo - key2",
        ],
        maxAge: 24 * 60 * 60 * 1000, // 24 hours
        httpOnly: false
})
);


app.use('/auth', authRouter);
app.use('/resources', resourcesRouter);
app.use('/admin', adminRouter);
// app.use('/solid-pod-lg', solidPodLghRouter);

app.listen(PORT, () => {
    console.log(
      `Solid API backend running on port [${PORT}].` + 
      `[${HOST}:${PORT}] `
    );
  });

module.exports = app;