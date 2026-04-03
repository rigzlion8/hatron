# Product Creation & Forms Search Results

## Overview
Comprehensive search results for all product creation components, forms, schemas, and image upload implementations in the Hatron ERP system.

---

## 1. FRONTEND PRODUCT COMPONENTS

### 1.1 Product Catalog Page
**File**: [frontend/src/app/dashboard/products/page.tsx](frontend/src/app/dashboard/products/page.tsx)

**Purpose**: Main product management interface with listing, creation, and editing capabilities

**Key Features**:
- Product grid view with search functionality
- Modal-based create/edit form
- Dynamic attributes system (for sizes, colors, etc.)
- Stock quantity integration from inventory module
- Category selection
- SKU management
- Price and cost fields (KES currency)
- Product image display (from `image_url` field)

**Form Fields**:
- Product Name (required, max 255 chars)
- SKU (optional, max 100 chars)
- Sales Price in KES (required, numeric)
- Cost in KES (optional, numeric)
- Category selection dropdown
- Dynamic Attributes (key-value pairs for variants)
- Image preview area

**State Management**:
- `products` - list of Product objects
- `categories` - ProductCategory list
- `quants` - stock quantities from inventory
- `showModal` - visibility toggle
- `editingProduct` - current form data
- `dynamicAttributes` - attribute key-value pairs
- `isSubmitting` - form submission state

**API Integration**:
- `GET /products?per_page=100` - fetch products with pagination
- `GET /products/categories` - fetch categories
- `GET /inventory/quants` - fetch stock quantities
- `POST /products` - create new product
- `PATCH /products/{product_id}` - update existing product

---

### 1.2 Sales Page (Product Usage in Orders)
**File**: [frontend/src/app/dashboard/sales/page.tsx](frontend/src/app/dashboard/sales/page.tsx)

**Purpose**: Sales order creation that integrates with products

**Product-Related Features**:
- Product dropdown selection in order lines
- Auto-population of product name and price
- Support for manual price override
- Quantity and discount per line item

**API Integration**:
- `GET /products?per_page=100` - fetch products for selection
- `POST /sales/orders` - create order with product line items

**Order Line Structure**:
```typescript
interface OrderLine {
  product_id: string;
  description: string;
  quantity: number;
  unit_price: number;
  discount: number;
}
```

---

### 1.3 POS Product Card Component
**File**: [frontend/src/components/pos/ProductCard.tsx](frontend/src/components/pos/ProductCard.tsx)

**Purpose**: Reusable product card for POS and e-commerce interfaces

**Features**:
- Product image display with fallback icon
- Product name and category display
- Price formatting in KES
- Hover effects and animations
- Click handler for add-to-cart functionality

**Props**:
```typescript
interface ProductCardProps {
  product: Product;
  onAdd: (product: Product) => void;
}

interface Product {
  id: string;
  name: string;
  price: number;
  category_name?: string;
  image_url?: string;
}
```

---

## 2. BACKEND PRODUCT MODELS

### 2.1 Product Model
**File**: [backend/modules/sales/models.py](backend/modules/sales/models.py)

**Database Table**: `products`

**Key Fields**:
- `id` - UUID primary key
- `tenant_id` - UUID foreign key (multi-tenancy)
- `name` - String(255), required
- `sku` - String(100), optional
- `type` - String(50): "storable", "consumable", or "service" (default: "storable")
- `category_id` - UUID foreign key to product_categories (nullable)
- `price` - Numeric(15,2), default 0.0
- `cost` - Numeric(15,2), default 0.0
- `image_url` - String(500), **nullable** (for product images)
- `description_sales` - Text, optional
- `attributes` - JSONB (flexible key-value pairs for variants)
- `is_active` - Boolean, default true
- `is_deleted` - Boolean, default false
- `created_at` - DateTime with timezone
- `updated_at` - DateTime with timezone

**Relationships**:
- `category` - Relationship to ProductCategory (lazy load with selectin)

---

### 2.2 ProductCategory Model
**File**: [backend/modules/sales/models.py](backend/modules/sales/models.py)

**Database Table**: `product_categories`

**Key Fields**:
- `id` - UUID primary key
- `tenant_id` - UUID foreign key
- `name` - String(255), required
- `parent_id` - UUID foreign key (self-referential, nullable) - supports hierarchical categories
- `description` - Text, optional
- `subcategories` - Relationship to child categories
- `parent` - Relationship to parent category

---

### 2.3 SalesOrderLine Model (Product Usage)
**File**: [backend/modules/sales/models.py](backend/modules/sales/models.py)

**Database Table**: `sales_order_lines`

**Product-Related Fields**:
- `product_id` - UUID foreign key to products (required)
- `description` - String, populated from product name
- `quantity` - Numeric
- `unit_price` - Numeric, can override product.price
- `discount` - Numeric percentage

---

## 3. BACKEND SCHEMAS (VALIDATION & SERIALIZATION)

### 3.1 Product Schemas
**File**: [backend/modules/sales/schemas.py](backend/modules/sales/schemas.py)

#### ProductCreate Schema
```python
class ProductCreate(BaseModel):
    name: str = Field(..., max_length=255)  # Required
    sku: Optional[str] = Field(None, max_length=100)
    type: str = Field(default="storable", pattern="^(storable|consumable|service)$")
    category_id: Optional[uuid.UUID] = None
    price: Decimal = Field(default=Decimal(0), ge=0)
    cost: Decimal = Field(default=Decimal(0), ge=0)
    description_sales: Optional[str] = None
    attributes: Optional[dict] = None
    # NOTE: image_url is NOT in create schema - needs separate upload handling
```

#### ProductUpdate Schema
```python
class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    sku: Optional[str] = Field(None, max_length=100)
    type: Optional[str] = Field(None, pattern="^(storable|consumable|service)$")
    category_id: Optional[uuid.UUID] = None
    price: Optional[Decimal] = Field(None, ge=0)
    cost: Optional[Decimal] = Field(None, ge=0)
    description_sales: Optional[str] = None
    attributes: Optional[dict] = None
    is_active: Optional[bool] = None
    # NOTE: image_url update also not here
```

#### ProductResponse Schema
```python
class ProductResponse(OrmBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    sku: Optional[str] = None
    type: str
    category_id: Optional[uuid.UUID] = None
    price: Decimal
    cost: Decimal
    description_sales: Optional[str] = None
    attributes: Optional[dict] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    category: Optional[ProductCategoryResponse] = None
    # NOTE: image_url NOT in response schema either
```

#### ProductCategoryCreate/Response Schemas
```python
class ProductCategoryCreate(BaseModel):
    name: str = Field(..., max_length=255)
    parent_id: Optional[uuid.UUID] = None
    description: Optional[str] = None

class ProductCategoryResponse(OrmBase):
    id: uuid.UUID
    name: str
    parent_id: Optional[uuid.UUID] = None
    description: Optional[str] = None
```

---

## 4. BACKEND API ENDPOINTS

### 4.1 Products Router
**File**: [backend/modules/sales/router.py](backend/modules/sales/router.py)

#### Product Endpoints

| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| POST | `/products` | Create new product | Required |
| GET | `/products` | List products (paginated) | Required |
| GET | `/products/{product_id}` | Get product details | Required |
| PATCH | `/products/{product_id}` | Update product | Required |

#### Product Parameters

**Create Product**:
- Request Body: `ProductCreate` schema
- Response: `ProductResponse` (201 Created)

**List Products**:
- Query Parameters:
  - `page: int` (default: 1, min: 1)
  - `per_page: int` (default: 20, min: 1, max: 100)
  - `category_id: Optional[UUID]` - filter by category
  - `search: Optional[str]` - search by name/sku
- Response: `PaginatedResponse[ProductResponse]`

**Get Product**:
- Path Parameter: `product_id: UUID`
- Response: `ProductResponse`

**Update Product**:
- Path Parameter: `product_id: UUID`
- Request Body: `ProductUpdate` schema
- Response: `ProductResponse`

#### Category Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/products/categories` | Create category |
| GET | `/products/categories` | List categories |

---

### 4.2 Sales Orders Router (Product Usage)
**File**: [backend/modules/sales/router.py](backend/modules/sales/router.py)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/sales/orders` | Create order with product lines |
| GET | `/sales/orders` | List orders |
| GET | `/sales/orders/{order_id}` | Get order details |
| PATCH | `/sales/orders/{order_id}` | Update order |
| POST | `/sales/orders/{order_id}/confirm` | Confirm order |

---

## 5. BACKEND SERVICE LAYER

### 5.1 SalesService
**File**: [backend/modules/sales/service.py](backend/modules/sales/service.py)

**Product Methods**:
```python
async def create_product(tenant_id: UUID, data: ProductCreate) -> ProductResponse
async def get_product(product_id: UUID, tenant_id: UUID) -> ProductResponse
async def list_products(tenant_id: UUID, page: int = 1, per_page: int = 20, 
                       category_id: Optional[UUID] = None, 
                       search: Optional[str] = None) -> PaginatedResponse[ProductResponse]
async def update_product(product_id: UUID, tenant_id: UUID, data: ProductUpdate) -> ProductResponse
```

---

## 6. IMAGE UPLOAD ANALYSIS

### 6.1 Current Image URL Implementation
**Status**: Images stored as URL strings only, no file upload endpoint

**Model Support**:
- `Product.image_url` - String(500) field in database
- Nullable and optional

**Frontend Display**:
- Used in ProductCard component with fallback icon
- Used in products page grid display
- Fallback to placeholder icon if no URL

**Backend Seeding**:
- [backend/modules/pos/seeds.py](backend/modules/pos/seeds.py) - contains hardcoded image URLs:
  - `/images/products/laptop.png`
  - `/images/products/mouse.png`
  - `/images/products/monitor.png`
  - `/images/products/coffee.png`
  - `/images/products/tea.png`
  - `/images/products/chocolate.png`
  - `/images/products/notebook.png`
  - `/images/products/pen.png`

### 6.2 File Upload Configuration (Not Yet Utilized)
**File**: [backend/settings.py](backend/settings.py)

**Configuration**:
```python
# File uploads
UPLOAD_DIR: str = "./uploads"
```

**Status**: Infrastructure exists but NOT actively used for product images

**Missing Components**:
- ❌ No file upload endpoint (POST /products/upload or similar)
- ❌ No `UploadFile` handling from FastAPI
- ❌ No image URL update endpoint
- ❌ No FormData support in frontend
- ❌ No file validation or processing logic
- ❌ No S3/cloud storage integration
- ❌ No image optimization/resizing

---

## 7. FRONTEND API CLIENT

### 7.1 API Configuration
**File**: [frontend/src/lib/api.ts](frontend/src/lib/api.ts)

**Base Configuration**:
```typescript
const API_URL = 
  typeof window !== 'undefined'
    ? '/api/v1'
    : (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1');

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});
```

**Auth Interceptor**: Automatically attaches Bearer JWT token from localStorage

**Status Tracking**: Console logging of all requests/responses with status codes

---

## 8. CURRENCY & FORMATTING

**Currency**: KES (Kenyan Shilling)

**Display Format**:
```typescript
const formatKES = (amount: number) => {
  return `KES ${amount.toLocaleString('en-KE', { 
    minimumFractionDigits: 2, 
    maximumFractionDigits: 2 
  })}`;
};
```

---

## 9. MULTI-TENANCY

**Tenant Isolation**:
- All product queries filtered by `tenant_id`
- User's tenant_id extracted from JWT token
- Database enforces foreign key to `tenants.id`

---

## 10. SUMMARY OF GAPS FOR IMAGE UPLOAD

To fully implement product image uploads, the following components are needed:

### Backend Improvements:
1. File upload endpoint (e.g., `POST /products/{product_id}/upload-image`)
2. Image storage service (local or cloud)
3. Image validation & resizing logic
4. Update to ProductUpdate schema to include image_url
5. CORS headers for image serving
6. Storage cleanup on product deletion

### Frontend Improvements:
1. File input component in product form
2. Image preview before upload
3. Drag-and-drop upload support
4. Upload progress indicator
5. Error handling for upload failures
6. File type/size validation
7. Multipart/form-data support in API client

---

## 11. KEY FILES REFERENCE

| File | Purpose | Type |
|------|---------|------|
| [frontend/src/app/dashboard/products/page.tsx](frontend/src/app/dashboard/products/page.tsx) | Main product management UI | Component |
| [frontend/src/app/dashboard/sales/page.tsx](frontend/src/app/dashboard/sales/page.tsx) | Sales order with products | Component |
| [frontend/src/components/pos/ProductCard.tsx](frontend/src/components/pos/ProductCard.tsx) | Product card display | Component |
| [backend/modules/sales/models.py](backend/modules/sales/models.py) | Product & Category models | Model |
| [backend/modules/sales/schemas.py](backend/modules/sales/schemas.py) | Pydantic validation schemas | Schema |
| [backend/modules/sales/router.py](backend/modules/sales/router.py) | API endpoints | Router |
| [backend/modules/sales/service.py](backend/modules/sales/service.py) | Business logic | Service |
| [backend/modules/sales/repository.py](backend/modules/sales/repository.py) | Database queries | Repository |
| [frontend/src/lib/api.ts](frontend/src/lib/api.ts) | Axios HTTP client | Utility |
| [backend/settings.py](backend/settings.py) | Configuration | Config |

---

## 12. EXISTING IMAGE PATTERNS

### In POS Module
**File**: [backend/modules/pos/seeds.py](backend/modules/pos/seeds.py)

Reference products with hardcoded image URLs showing the expected URL structure.

### In Frontend
- ProductCard component displays `product.image_url` with proper fallback
- Products page grid displays images in cards
- Both use `objectFit: 'contain'` for responsive sizing

---

## Architecture Notes

**Domain-Driven Design**: Products are in the Sales bounded context (sales module)

**Multi-Tenancy**: All queries scoped to current user's tenant_id

**API Pattern**: RESTful with pagination support

**Validation**: Pydantic schemas on both create and update

**Currency**: All numeric fields support 2 decimal places (Numeric(15,2))

**Timestamps**: All records track created_at and updated_at in UTC

