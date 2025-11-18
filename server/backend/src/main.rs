mod setup_database;

use std::{thread, time, str};
use rusqlite::{Connection, params, Result, ToSql};
use actix_cors::Cors;
use actix_web::{get, web, App, HttpServer, Responder, post, HttpResponse, error, HttpResponseBuilder};
use actix_web::web::Json;
use actix_files as fs;
use actix_web::http::header::ContentType;
use serde::{Deserialize, Serialize};
use r2d2_sqlite::{self, SqliteConnectionManager};
use chrono::{Datelike, DateTime, NaiveDateTime, Timelike, Utc};

#[derive(Deserialize)]
struct ButtonPress {
    kiosk_id: u32,
    button: u32,
    clientdate: Option<DateTime<Utc>>
}

#[derive(Debug, Serialize, Deserialize)]
struct Press {
    id: i32,
    kiosk_id: u32,
    button: u32,
    serverdate: NaiveDateTime,
}

#[derive(Deserialize)]
struct ButtonPressRequest {
    kiosk_id: u32,
    startdate: Option<DateTime<Utc>>,
    enddate: Option<DateTime<Utc>>,
}

#[derive(Serialize)]
struct Qotd {
    day: String,
    question: String,
}

type DbPool = r2d2::Pool<r2d2_sqlite::SqliteConnectionManager>;

#[post("/api/button_press/new")]
async fn button_press_new(
    pool: web::Data<DbPool>,
    button_press: web::Json<Vec<ButtonPress>>
) -> actix_web::Result<impl Responder> {

    // Obtaining a connection from the pool is also a potentially blocking operation.
    // So, it should be called within the `web::block` closure, as well.
    let conn = web::block(move || pool.get())
        .await?
        .map_err(error::ErrorInternalServerError)?;

    web::block(move || {
        for press in button_press.iter() {
            match conn.execute(
                "INSERT INTO press (kiosk_id, button, clientdate) VALUES (?1, ?2, ?3)",
                (
                    &press.kiosk_id,
                    &press.button,
                    &press.clientdate
                ),
            ) {
                Ok(updated) => println!("{} rows were inserted", updated),
                Err(err) => println!("insert failed: {}", err),
            };
        }
    })
        .await?;

    //let ten_millis = time::Duration::from_millis(2000);
    //thread::sleep(ten_millis);

    Ok(HttpResponse::Ok())

    // format!("\"kiosk_id\": haha{}, \"button\": haha{}",
    //         button_press.kiosk_id,
    //         button_press.button
    // )
}

#[get("/api/button_press")]
async fn button_press_json(
    pool: web::Data<DbPool>
) -> actix_web::Result<impl Responder> {

    // Obtaining a connection from the pool is also a potentially blocking operation.
    // So, it should be called within the `web::block` closure, as well.
    let conn = web::block(move || pool.get())
        .await?
        .map_err(error::ErrorInternalServerError)?;

    let mut stmt = conn.prepare("SELECT id, kiosk_id, button, serverdate FROM press").unwrap();
    let person_iter = stmt.query_map([], |row| {
        Ok(Press {
            id: row.get(0)?,
            kiosk_id: row.get(1)?,
            button: row.get(2)?,
            serverdate: row.get(3)?,
        })
    });
    let mut vec = Vec::new();
    for person in person_iter.unwrap() {
        vec.push(person.unwrap());
    }

    Ok(HttpResponse::Ok().json(vec))
}

#[post("/api/button_press/filter")]
async fn button_press_json_filter(
    pool: web::Data<DbPool>,
    button_press_request: web::Json<ButtonPressRequest>
) -> actix_web::Result<impl Responder> {

    // Obtaining a connection from the pool is also a potentially blocking operation.
    // So, it should be called within the `web::block` closure, as well.
    let conn = web::block(move || pool.get())
        .await?
        .map_err(error::ErrorInternalServerError)?;

    let mut stmt = conn.prepare("\
    SELECT id, kiosk_id, button, datetime(clientdate) \
    FROM press \
    WHERE kiosk_id = ?1 \
    AND datetime(clientdate) >= ?2 \
    AND datetime(clientdate) <= ?3 \
    ").unwrap();
    let person_iter = stmt.query_map(
        (&button_press_request.kiosk_id, &button_press_request.startdate, &button_press_request.enddate),
        |row| {
            Ok(Press {
                id: row.get(0)?,
                kiosk_id: row.get(1)?,
                button: row.get(2)?,
                serverdate: row.get(3)?,
            })
        }).ok();
    let mut vec = Vec::new();
    for person in person_iter.unwrap() {
        vec.push(person.unwrap());
    }

    Ok(HttpResponse::Ok().json(vec))
}

#[get("/api/kiosk/list")]
async fn kiosk_list(
    pool: web::Data<DbPool>
) -> actix_web::Result<impl Responder> {

    let conn = web::block(move || pool.get())
        .await?
        .map_err(error::ErrorInternalServerError)?;

    let mut stmt = conn.prepare("SELECT DISTINCT kiosk_id FROM press").unwrap();
    let iter = stmt.query_map([],|row| row.get(0)).unwrap();
    let mut vec = Vec::new();
    for kiosk_id in iter {
        let t: u32 = kiosk_id.unwrap();
        vec.push(t);
    }

    Ok(HttpResponse::Ok().json(vec))
}

#[get("/api/button_press/csv")]
async fn button_press_csv(
    pool: web::Data<DbPool>
) -> actix_web::Result<impl Responder> {

    let conn = web::block(move || pool.get())
        .await?
        .map_err(error::ErrorInternalServerError)?;

    let mut stmt = conn.prepare("SELECT id, kiosk_id, button, serverdate FROM press").unwrap();
    let person_iter = stmt.query_map([], |row| {
        Ok(Press {
            id: row.get(0)?,
            kiosk_id: row.get(1)?,
            button: row.get(2)?,
            serverdate: row.get(3)?,
        })
    });

    let mut wtr = csv::Writer::from_writer(vec![]);
    for person in person_iter.unwrap() {
        wtr.serialize(person.unwrap());
    }

    let data = String::from_utf8(wtr.into_inner().unwrap());
    Ok(
        HttpResponse::Ok()
            .append_header(("Content-Type", "text/csv"))
            .body(data.unwrap())
    )
}

#[get("/api/time")]
async fn get_time() -> actix_web::Result<impl Responder> {

    #[derive(Debug, Serialize)]
    struct TimeStruct {
        year: i32,
        month: u32,
        day: u32,
        hour: u32,
        minute: u32,
        second: u32
    }

    let dt = chrono::Utc::now();
    let ts = TimeStruct {
        year: dt.year(),
        month: dt.month(),
        day: dt.day(),
        hour: dt.hour(),
        minute: dt.minute(),
        second: dt.second()
    };

    Ok(HttpResponse::Ok().json(ts))
}

#[get("/api/kiosk/qotd/{day}")]
async fn kiosk_qotd(
    pool: web::Data<DbPool>,
    path: web::Path<String>
) -> actix_web::Result<impl Responder> {

    let day = path.into_inner();

    let conn = web::block(move || pool.get())
        .await?
        .map_err(error::ErrorInternalServerError)?;

    let mut stmt = conn.prepare("SELECT day, question FROM qotd WHERE day = ?1").unwrap();
    let iter = stmt.query_map([day],|row| row.get(1)).unwrap();
    let mut vec = Vec::new();
    for question in iter {
        let t: String = question.unwrap();
        vec.push(t);
    }

    Ok(HttpResponse::Ok().json(vec))
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {

    setup_database::setup_database("db.sqlite3").expect("Could not setup database");

    // connect to SQLite DB
    let manager = SqliteConnectionManager::file("db.sqlite3");
    let pool = r2d2::Pool::builder()
        .build(manager)
        .expect("database path should be valid path to SQLite DB file");
    let write_pool = r2d2::Pool::builder()
        .build(SqliteConnectionManager::file("db.sqlite3"))
        .expect("database path should be valid path to SQLite DB file");

    HttpServer::new(move || {
        let cors = Cors::permissive();

        App::new()
            .wrap(cors)
            .service(button_press_new)
            .service(button_press_json)
            .service(button_press_csv)
            .service(button_press_json_filter)
            .service(kiosk_list)
            .service(kiosk_qotd)
            .service(get_time)
            .service(fs::Files::new("/", "frontend/").index_file("index.html"))
            .app_data(web::JsonConfig::default().error_handler(|err, _req| {
                error::InternalError::from_response(
                    err, HttpResponse::BadRequest().into()).into()
            }))
            .app_data(web::Data::new(pool.clone()))
    })
    .bind(("0.0.0.0", 9898))?
    .run()
    .await
}