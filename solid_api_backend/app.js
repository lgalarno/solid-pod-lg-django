require('dotenv').config()

const cors = require('cors');
const express = require('express');
const bodyParser = require('body-parser');
const cookieSession = require("cookie-session");
const fileUpload = require('express-fileupload');

// const session = require('express-session')

const PORT_API = process.env.PORT_API
const HOST_API = process.env.HOST_API

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

app.use('/api/auth', authRouter);
app.use('/api/resources', resourcesRouter);
app.use('/api/admin', adminRouter);
// app.use('/solid-pod-lg', solidPodLghRouter);

app.listen(PORT_API, () => {
    console.log(
      `Solid API backend running on port [${PORT_API}].` + 
      `[${HOST_API}${PORT_API}] `
    );
  });

module.exports = app;
