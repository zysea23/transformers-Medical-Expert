import React from "react";
import styles from "./Card.module.scss";

const Card = ({ title, titleRight, children, className = "" }) => {
  return (
    <div className={`${styles.card} ${className}`}>
      {(title || titleRight) && (
        <div className={styles.cardHeader}>
          {title && <h3 className={styles.cardTitleTxt}>{title}</h3>}
          {titleRight && <div className={styles.cardTitleRight}>{titleRight}</div>}
        </div>
      )}
      <div className={styles.cardContent}>
        {children}
      </div>
    </div>
  );
};

export default Card;