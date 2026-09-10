import cv2
import easyocr
import numpy as np

def create_blind_schema(image_path, output_path):
    reader = easyocr.Reader(['fr', 'en'], gpu=False)
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Impossible de trouver l'image : {image_path}")
        
    mask = np.zeros(img.shape[:2], dtype="uint8")
    
    # --- NOUVEAU : PRÉ-PROCESSING (Nettoyage de la donnée visuelle) ---
    # 1. Conversion en niveaux de gris
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 2. Augmentation agressive du contraste (alpha = contraste, beta = luminosité)
    gray_contrasted = cv2.convertScaleAbs(gray, alpha=1.5, beta=20)
    
    # 3. Lecture avec un "mag_ratio" de 2.0 (l'IA zoome x2 en interne pour mieux lire les petits pixels)
    results = reader.readtext(gray_contrasted, mag_ratio=2.0)
    # ------------------------------------------------------------------
    
    boxes = []
    true_texts = []
    
    for (bbox, text, prob) in results:
        # On garde notre filtre de confiance
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
        true_texts.append(text)
        
    # L'effacement (Inpainting) se fait bien sur l'image 'img' d'origine pour garder les couleurs
    result_img = cv2.inpaint(img, mask, inpaintRadius=5, flags=cv2.INPAINT_TELEA)
    
    for i, box in enumerate(boxes):
        tl_x, tl_y, br_x, br_y = box
        c_x = int((tl_x + br_x) / 2)
        c_y = int((tl_y + br_y) / 2)
        
        cv2.circle(result_img, (c_x, c_y), 15, (50, 50, 50), -1)
        cv2.putText(result_img, str(i + 1), (c_x - 5, c_y + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
    cv2.imwrite(output_path, result_img)
    
    return true_texts
