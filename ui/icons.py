from PIL import Image, ImageDraw
import customtkinter as ctk

def generate_icons():
    """Generates icons programmatically using Pillow."""
    icons = {}
    # Colors suitable for light/dark blue theme
    colors = {"blue": "#3b82f6", "red": "#ef4444", "gray": "#64748b", "white": "#ffffff", "text": "#1e293b"}
    
    def draw_icon(name, color):
        size = (20, 20)
        img = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        if name == "folder":
            draw.polygon([(2,18), (2,6), (9,6), (11,4), (18,4), (18,18)], fill=color)
        
        elif name == "image":
            draw.rectangle([3,5,17,17], outline=color, width=2)
            draw.ellipse([5,7,8,10], fill=color)
            draw.polygon([(4,16), (8,12), (12,16)], fill=color)
            draw.polygon([(10,16), (14,12), (17,16)], fill=color)

        elif name == "list":
            for y in [6, 10, 14]:
                draw.rectangle([4, y, 16, y+2], fill=color)
            for y in [6, 10, 14]:
                draw.rectangle([2, y, 3, y+2], fill=color)

        elif name == "trash":
            draw.rectangle([6,6,14,17], fill=color) # bin
            draw.line([(5,5), (15,5)], fill=color, width=2) # lid line
            draw.rectangle([8,3,12,5], fill=color) # handle

        elif name == "save":
            draw.rectangle([4,4,16,16], fill=color)
            draw.rectangle([6,4,14,8], fill="#ffffff") # metal clip
            draw.rectangle([6,12,14,16], fill="#ffffff") # label

        elif name == "play":
            draw.polygon([(6,5), (6,15), (16,10)], fill=color)
            
        elif name == "gear":
            # Draw gear/cog icon
            import math
            cx, cy = 10, 10
            outer_radius = 7
            inner_radius = 4
            teeth = 8
            points = []
            for i in range(teeth * 2):
                angle = (i * 360 / (teeth * 2) - 90) * math.pi / 180
                radius = outer_radius if i % 2 == 0 else inner_radius
                x = cx + radius * math.cos(angle)
                y = cy + radius * math.sin(angle)
                points.append((x, y))
            draw.polygon(points, fill=color)
            draw.ellipse([cx-2, cy-2, cx+2, cy+2], fill="white")
            
        elif name == "logo":
            # Outer circle
            draw.ellipse([0,0,19,19], fill="#3b82f6")
            # Headphone band
            draw.arc([4,4,15,15], start=180, end=0, fill="white", width=2)
            # Book
            draw.rectangle([7,8,13,16], fill="white")
            # Earcups
            draw.rectangle([3,11,5,15], fill="white")
            draw.rectangle([14,11,16,15], fill="white")

        return ctk.CTkImage(img, size=(16, 16))

    icons['folder'] = draw_icon('folder', colors['blue'])
    icons['image'] = draw_icon('image', colors['gray'])
    icons['list'] = draw_icon('list', colors['gray'])
    icons['trash'] = draw_icon('trash', colors['red'])
    icons['save'] = draw_icon('save', colors['blue'])
    icons['play'] = draw_icon('play', colors['blue'])
    icons['gear'] = draw_icon('gear', colors['gray'])
    icons['logo'] = draw_icon('logo', colors['white'])
    
    return icons
