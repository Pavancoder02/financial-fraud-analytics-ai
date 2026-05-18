-- MySQL dump 10.13  Distrib 8.0.32, for Win64 (x86_64)
--
-- Host: localhost    Database: frauddetect
-- ------------------------------------------------------
-- Server version	8.0.32
SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";

CREATE DATABASE frauddetectdb ;
USE frauddetectdb;
--
-- Table structure for table `transactions`
--

DROP TABLE IF EXISTS `transactions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `transactions` (
  `fid` varchar(50) DEFAULT NULL,
  `gender` varchar(10) DEFAULT NULL,
  `age` int DEFAULT NULL,
  `bank_account_type` varchar(50) DEFAULT NULL,
  `bank_name` varchar(100) DEFAULT NULL,
  `transaction_amount` float DEFAULT NULL,
  `transaction_number` int DEFAULT NULL,
  `balance` float DEFAULT NULL,
  `transaction_type` varchar(50) DEFAULT NULL,
  `transaction_date` date DEFAULT NULL,
  `location` varchar(100) DEFAULT NULL,
  `trans_detection_type` varchar(150) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password` varchar(100) NOT NULL,
  `role` enum('remote_user','service_provider') NOT NULL,
  `gender` enum('Male','Female','Other') NOT NULL,
  `country` varchar(100) NOT NULL,
  `state` varchar(100) NOT NULL,
  `city` varchar(100) NOT NULL,
  `address` text NOT NULL,
  `mobile` varchar(10) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=MyISAM AUTO_INCREMENT=5 DEFAULT CHARSET=latin1;
