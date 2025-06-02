<?php
header("Content-Type: application/xml");
echo "<?xml version=\"1.0\" encoding=\"UTF-8\"?>";

require_once("../inc/db.php");

$conn = connectDB();

// Read query parameters
$searchName = isset($_GET['pokemon']) ? trim($_GET['pokemon']) : null;
$isRandom = isset($_GET['random']) && $_GET['random'] === "true";

// Start building SQL and params
$sql = "SELECT name, sprite_front_default, primary_type, secondary_type FROM pokemon";
$params = [];
$conditions = [];

// Add name filter if provided
if ($searchName !== null && $searchName !== "") {
    $conditions[] = "LOWER(name) LIKE LOWER($1)";
    $params[] = "%" . $searchName . "%";
}

// Add WHERE clause if needed
if (!empty($conditions)) {
    $sql .= " WHERE " . implode(" AND ", $conditions);
}

// Randomization or ordering
if ($isRandom) {
    $sql .= " ORDER BY RANDOM() LIMIT 1";
} else {
    $sql .= " ORDER BY \"order\" ASC";
}

// Execute query
$result = pg_query_params($conn, $sql, $params);

if (!$result || pg_num_rows($result) === 0) {
    echo "<pokemon_list></pokemon_list>"; // empty
    exit;
}

// Render response
if ($isRandom) {
    // Only one random Pokémon
    $row = pg_fetch_assoc($result);
    echo "<pokemon>";
    echo "<name>" . htmlspecialchars($row['name']) . "</name>";
    echo "<sprite>" . htmlspecialchars($row['sprite_front_default']) . "</sprite>";
    echo "<primary_type>" . htmlspecialchars($row['primary_type']) . "</primary_type>";
    echo "<secondary_type>" . htmlspecialchars($row['secondary_type']) . "</secondary_type>";
    echo "</pokemon>";
} else {
    // Full or filtered list
    echo "<pokemon_list>";
    while ($row = pg_fetch_assoc($result)) {
        echo "<pokemon>";
        echo "<name>" . htmlspecialchars($row['name']) . "</name>";
        echo "<sprite>" . htmlspecialchars($row['sprite_front_default']) . "</sprite>";
        echo "<primary_type>" . htmlspecialchars($row['primary_type']) . "</primary_type>";
        echo "<secondary_type>" . htmlspecialchars($row['secondary_type']) . "</secondary_type>";
        echo "</pokemon>";
    }
    echo "</pokemon_list>";
}
?>