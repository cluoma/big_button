use rusqlite::{Connection, Result};

pub(crate) fn setup_database(db_path: &str) -> Result<()> {
    let conn = Connection::open(db_path)?;

    conn.execute(
        "CREATE TABLE IF NOT EXISTS press (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            kiosk_id  INTEGER NOT NULL,
            button  INTEGER NOT NULL,
            serverdate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            clientdate TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )",
        (),
    )?;

    conn.execute(
        "CREATE TABLE IF NOT EXISTS qotd (
            day    TEXT NOT NULL PRIMARY KEY,
            question  TEXT NOT NULL
        )",
        (),
    )?;

    conn.close().expect("Could not close database");

    Ok(())
}