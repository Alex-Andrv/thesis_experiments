// Сортировка пузырьком
// Массив данных из k чисел
// Размер каждого из этих чисел - 1 байт

define k 5;
define n 4;

__in bit data[k][n];

__out bit sorted_data[k][n];

void main()
{
	for(int i = 0; i < k - 1; i = i + 1)
	{
		for(int j = 0; j < k - i - 1; j = j + 1)
		{
			if(data[j] > data[j + 1])
			{
				bit t[n] = data[j];
				data[j] = data[j+1];
				data[j+1] = t;
			}
		}
	}

	sorted_data = data;
}
