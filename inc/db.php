<?php
// This file provides a reusable function to connect to the PostgreSQL database.
// Include this file in any PHP script that needs database access.

function connectDB() {
    // Database connection parameters
    $host = "localhost";
    $port = "5432";
    $dbname = "pokemondb";
    $user = "postgres"; // Default PostgreSQL user; change if needed
    $password = "";     // Leave empty if no password is set

    // Build connection string
    $connStr = "host=$host port=$port dbname=$dbname user=$user password=$password";

    // Attempt to connect
    $conn = pg_connect($connStr);

    // Check for connection error
    if (!$conn) {
        // Send an HTTP 500 Internal Server Error if connection fails
        http_response_code(500);
        die("<error>Database connection failed.</error>");
    }

    // Return the open connection
    return $conn;
}
?>