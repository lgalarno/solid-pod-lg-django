require('dotenv').config()

const querystring = require('querystring');
const {
    getSessionFromStorage,
    getSessionIdFromStorageAll,
  } = require("@inrupt/solid-client-authn-node");

const {
    addUrl,
    addStringNoLocale,
    createSolidDataset,
    createThing,
    deleteSolidDataset,
    getBoolean,
    getContentType,
    getFile,
    getInteger,
    getPodUrlAll,
    getSolidDataset,
    getSourceUrl,
    getThing,
    getThingAll,
    getStringNoLocale,
    isContainer,
    isRawData,
    overwriteFile,
    removeThing,
    saveSolidDatasetAt,
    setThing
  } = require("@inrupt/solid-client")

const path = require('path');

const { SCHEMA_INRUPT, RDF, AS, POSIX, LDP} = require( "@inrupt/vocab-common-rdf")

const express = require('express');
const router = express.Router();
const fetch = require("node-fetch");


router.post("/fetch", async (req, res, next) => {
    console.log('fetch')
    console.log('req.body: ' + req.body)
    let obj = await initFetch(req.body)  // obj contains session, resourceURL, status, content, text, ContentType
    if (obj.valid === true) {
        try {
            const resp = await obj.session.fetch(obj.resourceURL)
            obj.ContentType = resp.headers.get("content-type")
            console.log('content_type: ' + obj.ContentType)
            obj.status = resp.status
            console.log(resp.status)
            if (obj.status === 200) {
                // res.type(content_type)
                // obj.content = await resp.text()
                if (obj.ContentType.includes('text/turtle') ) {
                    obj.content = await resp.text()
                } else {
                    if (resp.status === 200) {  // send only ttl file here, otherwise, error 400
                        obj.status = 400
                        obj.text = `Invalid file type ${obj.content_type}: not a ttl file.`
                    }
                }
            } else {
                obj.text = resp.statusText  // get statusText from solid=client
            }
        } catch(err) {
            obj.status = 500
            obj.text = `An error occurred getting - ${obj.resourceURL} -. Please, double check the url.`
        }
    }
    // res.status(obj.status)
    delete obj.session
    return res.send(JSON.stringify(obj));
});

router.get("/download", async (req, res, next) => {
    console.log('download')
    let obj = await initFetch(req.query)  // obj contains session, resourceURL, response status, response content
    if (obj.valid === true) {
        try {
            const file = await getFile(
                obj.resourceURL,               // File in Pod to Read
                { fetch: obj.session.fetch }       // fetch from authenticated session
            );
            const arrayBuffer = await file.arrayBuffer();
            const filename = path.parse(obj.resourceURL).base;
            const parent = path.dirname(obj.resourceURL)

            console.log('contentType: ' + getContentType(file))
            res.contentType(getContentType(file));
            res.set("Content-Disposition", "attachment;filename=" + filename)
            obj.status = 200
            obj.content = new Buffer(arrayBuffer)
        } catch (err) {
            obj.status = err.statusCode
            obj.content = `Error ${err.statusCode}: ${err.statusText}`
        }
    }
    res.status(obj.status)
    return res.send(obj.content);
    });


router.post("/upload", async (req, res, next) => {
    console.log('upload')
    const json_data = JSON.parse(req.body.json_data)
    const file = req.files.file
    const new_resourceURL = json_data.resourceURL + file.name

    // req.query.sessionId = json_data.sessionId
    // req.query.resource = json_data.current_resource

    let obj = await initFetch(json_data)  // obj contains session, resourceURL, response status, response content
    if (obj.valid === true) {
        const savedFile = await overwriteFile(
            new_resourceURL,                   // URL for the file.
            file.data,                        // Buffer containing file data
            { contentType: file.mimetype, fetch: obj.session.fetch } // mimetype if known, fetch from the authenticated session
        );
        obj.status = 201
        obj.text = `${new_resourceURL} created`

        try {
            const savedFile = await overwriteFile(
                new_resourceURL,                   // URL for the file.
                file.data,                        // Buffer containing file data
                { contentType: file.mimetype, fetch: obj.session.fetch } // mimetype if known, fetch from the authenticated session
            );
            obj.status = 201
            obj.text = `${new_resourceURL} created`
        } catch (err) {
            obj.status = 500
            obj.text = `${err.statusText}`
        }
    }
    delete obj.session
    console.log(JSON.stringify(obj))
    return res.send(JSON.stringify(obj));
});


router.post("/delete", async (req, res, next) => {
    console.log('delete')
    let obj = await initFetch(req.body)  // obj contains session, resourceURL, response status, response content
    if (obj.valid === true) {
        try {
            await deleteSolidDataset(
                obj.resourceURL, 
                { fetch: obj.session.fetch }           // fetch function from authenticated session
              );

            obj.status = 205
            obj.text = `${obj.resourceURL} deleted`
        } catch (err) {
            obj.status = err.statusCode
            obj.text = `Error ${err.statusCode}: ${err.statusText}`
        }
    }
    delete obj.session
    console.log(JSON.stringify(obj))
    return res.send(JSON.stringify(obj));
});

router.get("/getpodurl", async (req, res, next) => {
    console.log('getpodurl')
    let obj = await initFetch(req)  // obj contains session, resourceURL, response status, response content
    if (obj.valid === true) {
        try {
            const mypods = await getPodUrlAll(obj.session.info.webId, { fetch: obj.session.fetch });
            console.log('typeof: ' + typeof mypods)
            if (mypods == '') {
                console.log('Empty')
                  try {
                    let ds = await getSolidDataset(url)
                    let thing = ds && getThing(ds, url)
                    let storageUrl = thing && getUrl(thing, 'http://www.w3.org/ns/pim/space#storage')
                    if (storageUrl) return storageUrl;
                  } catch (_ignored) { }

            } else if (typeof mypods === "undefined") {
                console.log('undefined')
            } else if (mypods.length === 0) {
                console.log('length 0')
            }


            console.log('mypods: ' + mypods)
            obj.status = 200
            obj.content = mypods
        } catch (err) {
            obj.status = err.statusCode
            obj.content = `Error ${err.statusCode}: ${err.statusText}`
        }
    }
    res.status(obj.status)
    return res.send(obj.content);
    });


router.get("/test", async (req, res, next) => {
    console.log('test')

    let obj = await initFetch(req)  // obj contains session, resourceURL, response status, response content
    if (obj.valid === true) {
        const myDataset = await getSolidDataset(
        obj.resourceURL,
        { fetch: fetch }  // fetch function from authenticated session
        );

        let items = getThingAll(myDataset);
        items.forEach((item) => {
            const i = getInteger(item, POSIX.size);
            console.log(item.url)
            console.log(i)
            console.log(isContainer(item.url))
        });
        // const containers = getThing(myDataset, LDP.Container)
        // console.log(containers)
        // containers.forEach((container) => {
        //     console.log(container)
        // });
        // let g= myDataset.graphs

        // console.log(await (await session.fetch(resourceURL)).text());
        try {
            resp = await obj.session.fetch(obj.resourceURL)
            const content_type  = resp.headers.get("content-type")
            res.type(content_type)
            obj.status = resp.status
            obj.content = await resp.text()
        } catch(e) {
            obj.status = 500
            obj.content = `An error occurred getting - ${obj.resourceURL} -. Please, double check the url.`
        } 
    }

    res.status(obj.status)
    return res.send(obj.content);
});

    async function initFetch(r) {
        let obj = {}
        obj.valid = true
        console.log('sessionId: ' + r.sessionId)
        obj.session = await getSessionFromStorage(r.sessionId);
        if (typeof obj.session === "undefined") {
            obj.valid = false
            obj.status = 500
            obj.text = `No session found.`  // 'No session found. Please, log in to your pod provider again.'
        }
        console.log('resource: ' + r.resourceURL)
        if (typeof r.resourceURL === "undefined") {
            obj.valid = false
            obj.status = 500
            obj.text = "Pass the (encoded) URL of the Resource using `?resource=&lt;resource URL&gt;`."  //'Please pass the (encoded) URL of the Resource you want to fetch using `?resource=&lt;resource URL&gt;`.'
        }
        obj.resourceURL = r.resourceURL
        return obj
    }

module.exports = router;