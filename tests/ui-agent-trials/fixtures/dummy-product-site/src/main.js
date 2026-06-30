import products from './products.js';

const productList = document.getElementById('product-list');

if (products.length === 0) {
  const emptyState = document.createElement('p');
  emptyState.textContent = 'No products available.';
  productList.appendChild(emptyState);
} else {
  products.forEach(product => {
    const productCard = document.createElement('div');
    productCard.classList.add('product-card');

    const productName = document.createElement('h2');
    productName.textContent = product.name;

    const productCategory = document.createElement('p');
    productCategory.textContent = `Category: ${product.category}`;

    const productDescription = document.createElement('p');
    productDescription.textContent = `Description: ${product.description}`;

    const productPrice = document.createElement('p');
    productPrice.textContent = `Price: $${product.price.toFixed(2)}`;

    productCard.appendChild(productName);
    productCard.appendChild(productCategory);
    productCard.appendChild(productDescription);
    productCard.appendChild(productPrice);

    productList.appendChild(productCard);
  });
}
