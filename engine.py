import cv2
import easyocr
import numpy as np

def create_blind_schema(image_path, output_path):
    reader = easyocr.Reader(['fr', 'en'], gpu=False)
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Impossible de trouver l'image : {image_path}")
        
    mask = np.zeros(img.shape[:2], dtype="uint8")
    results = reader.readtext(image_path)
    
    boxes = []
    true_texts = [] # Pour stocker les vraies réponses
    
    for (bbox, text, prob) in results:
        # FILTRE : Si l'IA est sûre à moins de 25%, on ignore (évite les fausses détections)
        if prob < 0.25:
            continue
            
        (tl, tr, br, bl) = bbox
        tl_x, tl_y = int(tl[0]), int(tl[1])
        br_x, br_y = int(br[0]), int(br[1])
        
        padding = 3
        tl_x, tl_y = max(0, tl_x - padding), max(0, tl_y - padding)
        br_x, br_y = min(img.shape[1], br_x + padding), min(img.shape[0], br_y + padding)
        
        cv2.rectangle(mask, (tl_x, tl_y), (br_x, br_y), 255, -1)
        boxes.append((tl_x, tl_y, br_x, br_y))
        true_texts.append(text) # On sauvegarde le vrai mot
        
    # Effacement du texte
    result_img = cv2.inpaint(img, mask, inpaintRadius=5, flags=cv2.INPAINT_TELEA)
    
    # Ajout des pastilles numérotées sur l'image nettoyée
    for i, box in enumerate(boxes):
        tl_x, tl_y, br_x, br_y = box
        c_x = int((tl_x + br_x) / 2)
        c_y = int((tl_y + br_y) / 2)
        
        cv2.circle(result_img, (c_x, c_y), 15, (50, 50, 50), -1)
        cv2.putText(result_img, str(i + 1), (c_x - 5, c_y + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
    cv2.imwrite(output_path, result_img)
    
    # On renvoie la liste des mots originaux pour la correction
    return true_texts