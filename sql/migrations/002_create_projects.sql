CREATE TABLE IF NOT EXISTS projects (
  project_id INT PRIMARY KEY AUTO_INCREMENT,
  project_name VARCHAR(255) NOT NULL,
  start_date DATE,
  end_date DATE
);