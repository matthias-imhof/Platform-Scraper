CREATE TABLE `users` (
  `id` varchar(36) PRIMARY KEY,
  `firstname` varchar(255),
  `lastname` varchar(255),
  `role` varchar(255),
  `joined_on` timestamp,
  `last_online` timestamp,
  `response_time_hours` float,
  `age` integer,
  `gender` varchar(255),
  `race` varchar(255),
  `profile_description` text,
  `wage` float,
  `normalized_rating` float,
  `original_rating` float,
  `profile_id` varchar(255),
  `picture_url` varchar(255),
  `profile_url` varchar(255),
  `gigs` integer,
  `has_cv_uploaded` boolean,
  `has_references_uploaded` integer,
  `verified` boolean,
  `favorised` integer,
  `professional_subscription` boolean,
  `experience_in_years` integer,
  `spoken_language_codes` text,
  `scraped_at` timestamp,
  `ranking_id` varchar(36),
  `platform_id` varchar(36),
  `location_id` varchar(36)
);

CREATE TABLE `platforms` (
  `id` varchar(36) PRIMARY KEY,
  `platform_name` varchar(255),
  `platform_link` varchar(255),
  `min_rating_reviews` float,
  `max_rating_reviews` float,
  `min_rating_references` float,
  `max_rating_references` float,
  `min_rating_users` float,
  `max_rating_users` float,
  `metadata` varchar(255)
);

CREATE TABLE `locations` (
  `id` varchar(36) PRIMARY KEY,
  `address` varchar(255),
  `plz` varchar(255),
  `city` varchar(255)
);

CREATE TABLE `ranking` (
  `id` varchar(36) PRIMARY KEY,
  `position_on_site` integer,
  `search_query_id` varchar(36),
  `scraped_at` timestamp,
  `platform_id` varchar(36),
  `user_id` varchar(36)
);

CREATE TABLE `search_query` (
  `id` varchar(36) PRIMARY KEY,
  `city` varchar(255),
  `plz` varchar(255),
  `radius` integer,
  `filter` text,
  `scraping_4_PLZ` boolean
);

CREATE TABLE `reviews` (
  `id` varchar(36) PRIMARY KEY,
  `title` varchar(255),
  `normalized_rating` float,
  `original_rating` float,
  `description` text,
  `author_id` varchar(36),
  `reviewee_id` varchar(36)
);

CREATE TABLE `references` (
  `id` varchar(36) PRIMARY KEY,
  `title` varchar(255),
  `firstname` varchar(255),
  `lastname` varchar(255),
  `description` text,
  `relationship` varchar(255),
  `author_id` varchar(36),
  `referencee_id` varchar(36)
);

CREATE TABLE `gigs` (
  `id` varchar(36) PRIMARY KEY,
  `title` varchar(255),
  `type_of_job` varchar(255),
  `created_at` timestamp,
  `gig_date` timestamp,
  `wage` float,
  `description` text,
  `author_id` varchar(36),
  `agent_id` varchar(36),
  `platform_id` varchar(36),
  `scraped_at` timestamp,
  `search_query_id` varchar(36),
  `location_id` varchar(36)
);

ALTER TABLE `users` ADD FOREIGN KEY (`location_id`) REFERENCES `locations` (`id`);

ALTER TABLE `users` ADD FOREIGN KEY (`ranking_id`) REFERENCES `ranking` (`id`);

ALTER TABLE `gigs` ADD FOREIGN KEY (`author_id`) REFERENCES `users` (`id`);

ALTER TABLE `gigs` ADD FOREIGN KEY (`agent_id`) REFERENCES `users` (`id`);

ALTER TABLE `gigs` ADD FOREIGN KEY (`location_id`) REFERENCES `locations` (`id`);

ALTER TABLE `gigs` ADD FOREIGN KEY (`search_query_id`) REFERENCES `search_query` (`id`);

ALTER TABLE `ranking` ADD FOREIGN KEY (`search_query_id`) REFERENCES `search_query` (`id`);

ALTER TABLE `reviews` ADD FOREIGN KEY (`reviewee_id`) REFERENCES `users` (`id`);

ALTER TABLE `reviews` ADD FOREIGN KEY (`author_id`) REFERENCES `users` (`id`);

ALTER TABLE `references` ADD FOREIGN KEY (`author_id`) REFERENCES `users` (`id`);

ALTER TABLE `references` ADD FOREIGN KEY (`referencee_id`) REFERENCES `users` (`id`);

ALTER TABLE `ranking` ADD FOREIGN KEY (`platform_id`) REFERENCES `platforms` (`id`);

ALTER TABLE `users` ADD FOREIGN KEY (`platform_id`) REFERENCES `platforms` (`id`);

ALTER TABLE `gigs` ADD FOREIGN KEY (`platform_id`) REFERENCES `platforms` (`id`);
